import csv
import json
import math
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Tuple

BOARD_RADIUS_MM = 170.0
CSV_HEADER = ["timestamp", "code", "x_mm", "y_mm", "turn_state"]


class TrainingClient:
    """Lightweight logger for training throws with a live dartboard view."""

    def __init__(self, log_path: str, master: Optional[tk.Misc] = None, board_image_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.abspath(log_path))
        training_dir = os.path.join(base_dir, "training_logs")
        os.makedirs(training_dir, exist_ok=True)
        self.log_path = os.path.join(training_dir, os.path.basename(log_path))

        self.master = master or tk.Tk()
        self._owns_master = master is None
        self.board_image_path = board_image_path or os.path.join(os.path.dirname(__file__), "DartBoard.png")
        self.calibration_path = f"{self.board_image_path}.calibration.json"

        self._lock = threading.Lock()
        self.throws: List[dict] = []
        self.selected_index: Optional[int] = None
        self.nudge_step_mm = 0.2
        self.marker_radius_px = 3
        self._calibrating_stage: Optional[int] = None
        self._cal_center: Optional[Tuple[float, float]] = None
        self.mean_xy: Tuple[float, float] = (0.0, 0.0)
        default_var = (BOARD_RADIUS_MM / 4) ** 2
        self.cov_matrix: Tuple[Tuple[float, float], Tuple[float, float]] = (
            (default_var, 0.0),
            (0.0, default_var),
        )
        self._show_contours = tk.BooleanVar(value=True)

        self._load_existing()
        self._update_distribution_stats()
        self._build_ui()
        self._refresh_view()

    # -------- File helpers --------

    def _load_existing(self):
        if not os.path.exists(self.log_path):
            return

        try:
            with open(self.log_path, newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and set(reader.fieldnames) >= {"timestamp", "code", "x_mm", "y_mm"}:
                    for row in reader:
                        self._add_throw(
                            timestamp=row.get("timestamp") or time.strftime("%Y-%m-%d %H:%M:%S"),
                            code=row.get("code", ""),
                            x_mm=float(row.get("x_mm", "0")),
                            y_mm=float(row.get("y_mm", "0")),
                            turn_state=row.get("turn_state", ""),
                            persist=False,
                            select=False,
                            refresh=False,
                        )
                elif reader.fieldnames and "turn_state" in reader.fieldnames:
                    for row in reader:
                        self._append_from_turn_state(row.get("turn_state", ""), timestamp=row.get("timestamp"), persist=False, refresh=False)
        except Exception:
            # If legacy format cannot be read, start fresh
            self.throws = []
            self.selected_index = None

    def _persist_log(self) -> Optional[str]:
        with self._lock:
            rows = list(self.throws)
        if not rows:
            try:
                if os.path.exists(self.log_path):
                    os.remove(self.log_path)
            except Exception:
                pass
            return None
        try:
            with open(self.log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADER)
                for entry in rows:
                    writer.writerow(
                        [
                            entry["timestamp"],
                            entry["code"],
                            f"{entry['x_mm']:.3f}",
                            f"{entry['y_mm']:.3f}",
                            entry.get("turn_state", ""),
                        ]
                    )
        except Exception as exc:
            return str(exc)
        return None

    # -------- UI --------

    def _build_ui(self):
        self.window = self.master if self._owns_master else tk.Toplevel(self.master)
        self.window.title("Training Darts")
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self.board_image = tk.PhotoImage(file=self.board_image_path)
        except Exception:
            self.board_image = None

        board_width = self.board_image.width() if self.board_image else 600
        board_height = self.board_image.height() if self.board_image else 600
        self._init_board_geometry(board_width, board_height)

        top = tk.Frame(self.window)
        top.pack(side="top", fill="x")

        self.count_var = tk.StringVar(value="Throws: 0")
        self.selected_var = tk.StringVar(value="Selected: None")
        tk.Label(top, textvariable=self.count_var).pack(side="left", padx=5)
        tk.Label(top, textvariable=self.selected_var).pack(side="left", padx=5)

        controls = tk.Frame(self.window)
        controls.pack(side="top", fill="x", pady=4)
        tk.Button(controls, text="Undo Last", command=self.undo_last).pack(side="left", padx=5)
        tk.Button(controls, text="Load CSV", command=self._load_from_dialog).pack(side="left", padx=5)
        tk.Button(controls, text="Calibrate Board", command=self._start_calibration).pack(side="left", padx=5)
        tk.Checkbutton(controls, text="Show Contours", variable=self._show_contours, command=self._schedule_refresh).pack(side="left", padx=5)
        tk.Label(controls, text="Use arrow keys to nudge selected dart").pack(side="left")

        self.canvas = tk.Canvas(self.window, width=board_width, height=board_height, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        if self.board_image:
            self.canvas.create_image(0, 0, image=self.board_image, anchor="nw", tags=("background",))

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.window.bind("<Left>", lambda e: self._nudge_selected(-self.nudge_step_mm, 0))
        self.window.bind("<Right>", lambda e: self._nudge_selected(self.nudge_step_mm, 0))
        self.window.bind("<Up>", lambda e: self._nudge_selected(0, self.nudge_step_mm))
        self.window.bind("<Down>", lambda e: self._nudge_selected(0, -self.nudge_step_mm))
        try:
            self.window.focus_set()
        except Exception:
            pass

    def _init_board_geometry(self, board_width: float, board_height: float):
        diameter_px = min(board_width, board_height)
        cx = board_width / 2
        cy = board_height / 2
        saved = self._load_calibration_data()
        if saved:
            cx = saved.get("center", [cx, cy])[0]
            cy = saved.get("center", [cx, cy])[1]
            diameter_px = saved.get("diameter_px", diameter_px)
        self.px_per_mm = diameter_px / (2 * BOARD_RADIUS_MM)
        self.board_cx = cx
        self.board_cy = cy

    def _load_calibration_data(self) -> Optional[dict]:
        if not os.path.exists(self.calibration_path):
            return None
        try:
            with open(self.calibration_path, "r") as f:
                data = json.load(f)
            if "center" in data and "diameter_px" in data and data["diameter_px"] > 0:
                return data
        except Exception:
            return None
        return None

    def _save_calibration_data(self, cx: float, cy: float, diameter_px: float):
        data = {"center": [cx, cy], "diameter_px": diameter_px}
        try:
            with open(self.calibration_path, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _on_close(self):
        if self._owns_master:
            self.master.destroy()
        else:
            self.window.destroy()

    def _refresh_view(self):
        with self._lock:
            throws = list(self.throws)
            selected = self.selected_index
            mean_xy = self.mean_xy
            cov = self.cov_matrix
            show_contours = self._show_contours.get()

        try:
            self.canvas.delete("dart_point")
            self.canvas.delete("contour")
        except tk.TclError:
            return

        if show_contours and cov is not None and cov[0][0] >= 0 and cov[1][1] >= 0:
            self._draw_contours(mean_xy, cov)

        for idx, entry in enumerate(throws):
            px, py = self._mm_to_canvas(entry["x_mm"], entry["y_mm"])
            r = self.marker_radius_px
            color = "red" if idx == selected else "#6bffff"
            item = self.canvas.create_oval(px - r, py - r, px + r, py + r, fill=color, outline="black", width=1, tags=("dart_point", f"idx_{idx}"))
            self.canvas.tag_bind(item, "<Button-1>", self._on_point_click)

        self.count_var.set(f"Throws: {len(throws)}")
        if selected is None or selected >= len(throws):
            self.selected_var.set("Selected: None")
        else:
            entry = throws[selected]
            self.selected_var.set(
                f"Selected: #{selected + 1} {entry['code']} ({entry['x_mm']:.1f} mm, {entry['y_mm']:.1f} mm)"
            )

    def _schedule_refresh(self):
        if threading.current_thread() is threading.main_thread():
            self._refresh_view()
        else:
            try:
                self.master.after(0, self._refresh_view)
            except Exception:
                pass

    # -------- Coordinate helpers --------

    def _mm_to_canvas(self, x_mm: float, y_mm: float) -> Tuple[float, float]:
        return (
            self.board_cx + x_mm * self.px_per_mm,
            self.board_cy - y_mm * self.px_per_mm,
        )

    def _draw_contours(self, mean_xy: Tuple[float, float], cov: Tuple[Tuple[float, float], Tuple[float, float]]):
        a, c = cov[0]
        _, b = cov[1]
        trace = a + b
        det = a * b - c * c
        disc = max(trace * trace / 4 - det, 0.0)
        root = math.sqrt(disc)
        eig1 = trace / 2 + root
        eig2 = trace / 2 - root
        if eig1 <= 0 or eig2 <= 0:
            return
        if abs(c) > 1e-9:
            v1 = (eig1 - b, c)
        else:
            v1 = (1.0, 0.0) if a >= b else (0.0, 1.0)
        norm = math.hypot(v1[0], v1[1])
        if norm == 0:
            return
        v1 = (v1[0] / norm, v1[1] / norm)
        v2 = (-v1[1], v1[0])

        levels = [(1, "green"), (2, "orange"), (3, "red")]
        cx_mm, cy_mm = mean_xy

        for k, color in levels:
            rx = k * math.sqrt(eig1)
            ry = k * math.sqrt(eig2)
            points = []
            for deg in range(0, 360, 12):
                rad = math.radians(deg)
                local_x = rx * math.cos(rad)
                local_y = ry * math.sin(rad)
                world_x = cx_mm + local_x * v1[0] + local_y * v2[0]
                world_y = cy_mm + local_x * v1[1] + local_y * v2[1]
                px, py = self._mm_to_canvas(world_x, world_y)
                points.extend([px, py])
            if points:
                try:
                    self.canvas.create_polygon(points, outline=color, fill="", width=2, tags=("contour",))
                except Exception:
                    pass

    # -------- Event handlers --------

    def _on_point_click(self, event):
        if self._calibrating_stage is not None:
            return
        tags = self.canvas.gettags(event.widget.find_closest(event.x, event.y)[0])
        for t in tags:
            if t.startswith("idx_"):
                idx = int(t.split("_", 1)[1])
                with self._lock:
                    if 0 <= idx < len(self.throws):
                        self.selected_index = idx
                break
        self._schedule_refresh()

    def _on_canvas_click(self, event):
        if self._calibrating_stage is not None:
            if self._calibrating_stage == 0:
                self._cal_center = (event.x, event.y)
                self._calibrating_stage = 1
                self.selected_var.set("Calibration: now click the outer double ring edge")
            else:
                if not self._cal_center:
                    self._calibrating_stage = None
                    return
                cx, cy = self._cal_center
                dist = math.dist((cx, cy), (event.x, event.y))
                if dist > 0:
                    diameter_px = 2 * dist
                    self.board_cx = cx
                    self.board_cy = cy
                    self.px_per_mm = diameter_px / (2 * BOARD_RADIUS_MM)
                    self._save_calibration_data(cx, cy, diameter_px)
                    self.selected_var.set("Calibration saved")
                self._calibrating_stage = None
                self._cal_center = None
                self._refresh_view()
            return
        # Selecting nearest dart to click helps tweak positions
        closest = self.canvas.find_closest(event.x, event.y)
        if closest:
            self._on_point_click(type("evt", (), {"widget": self.canvas, "x": event.x, "y": event.y}))

    # -------- Public API --------

    def log_throw(self, turn_state: str) -> Optional[str]:
        """Append a training throw to memory, file, and GUI."""
        try:
            entry = self._append_from_turn_state(turn_state, persist=False, refresh=False)
            if entry is None:
                return "Invalid dart event"
            return self._after_data_change(persist=True)
        except Exception as exc:
            return str(exc)

    def undo_last(self):
        with self._lock:
            if not self.throws:
                return
            self.throws.pop()
            if self.selected_index is not None:
                self.selected_index = min(self.selected_index, len(self.throws) - 1)
        self._after_data_change(persist=True)

    def load_csv_file(self, file_path: str) -> Optional[str]:
        if not file_path:
            return "No file selected"
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return "File not found"
        with self._lock:
            self.log_path = abs_path
            self.throws = []
            self.selected_index = None
        self._load_existing()
        return self._after_data_change(persist=False)

    # -------- Internal helpers --------

    def _append_from_turn_state(self, turn_state: str, timestamp: Optional[str] = None, persist: bool = True, refresh: bool = True) -> Optional[dict]:
        if not turn_state.startswith("dart:"):
            return None
        parts = turn_state.split()
        if len(parts) < 3:
            return None
        code = parts[0].split(":", 1)[1]
        try:
            x_mm = float(parts[1])
            y_mm = float(parts[2])
        except ValueError:
            return None

        return self._add_throw(
            timestamp or time.strftime("%Y-%m-%d %H:%M:%S"),
            code,
            x_mm,
            y_mm,
            turn_state=turn_state,
            persist=persist,
            select=True,
            refresh=refresh,
        )

    def _add_throw(self, timestamp: str, code: str, x_mm: float, y_mm: float, turn_state: str = "", persist: bool = False, select: bool = True, refresh: bool = True) -> dict:
        entry = {"timestamp": timestamp, "code": code, "x_mm": x_mm, "y_mm": y_mm, "turn_state": turn_state}
        with self._lock:
            self.throws.append(entry)
            if select:
                self.selected_index = len(self.throws) - 1
        if persist:
            self._persist_log()
        if refresh:
            self._schedule_refresh()
        return entry

    def _nudge_selected(self, dx_mm: float, dy_mm: float):
        with self._lock:
            if self.selected_index is None or not self.throws:
                return
            idx = self.selected_index
            self.throws[idx]["x_mm"] += dx_mm
            self.throws[idx]["y_mm"] += dy_mm
        self._after_data_change(persist=True)

    def _after_data_change(self, persist: bool) -> Optional[str]:
        self._update_distribution_stats()
        error = self._persist_log() if persist else None
        self._schedule_refresh()
        return error

    def _update_distribution_stats(self):
        with self._lock:
            count = len(self.throws)
            if count < 2:
                default_var = (BOARD_RADIUS_MM / 4) ** 2
                self.mean_xy = (0.0, 0.0)
                self.cov_matrix = ((default_var, 0.0), (0.0, default_var))
                return
            xs = [t["x_mm"] for t in self.throws]
            ys = [t["y_mm"] for t in self.throws]
            mean_x = sum(xs) / count
            mean_y = sum(ys) / count
            var_x = sum((x - mean_x) ** 2 for x in xs) / count
            var_y = sum((y - mean_y) ** 2 for y in ys) / count
            cov_xy = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(count)) / count
            self.mean_xy = (mean_x, mean_y)
            self.cov_matrix = ((var_x, cov_xy), (cov_xy, var_y))

    @staticmethod
    def _format_turn_state(code: str, x_mm: float, y_mm: float) -> str:
        return f"dart:{code} {x_mm:.3f} {y_mm:.3f}"

    # -------- UI callbacks --------

    def _load_from_dialog(self):
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Load Training CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=os.path.dirname(self.log_path),
        )
        if not file_path:
            return
        err = self.load_csv_file(file_path)
        if err:
            try:
                messagebox.showerror("Load Failed", err, parent=self.window)
            except Exception:
                pass

    def _start_calibration(self):
        self._calibrating_stage = 0
        self._cal_center = None
        self.selected_var.set("Calibration: click the board center")
