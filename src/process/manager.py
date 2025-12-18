import subprocess
import os
import threading
import time
from typing import List, Dict
from aedificator import console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from aedificator.paths import get_logs_dir


class ProcessManager:
    """Manages background processes and live output display."""

    @staticmethod
    def display_live_output(process_info: List[Dict], safe_decode_fn):
        """Display live output from multiple processes with split-screen layout."""
        log_dir = get_logs_dir()

        log_files = []
        for proc_info in process_info:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = os.path.join(log_dir, f"{proc_info['name'].replace(' ', '_')}_{timestamp}.log")
            log_file = open(log_filename, 'w', encoding='utf-8', errors='replace')
            proc_info['log_file'] = log_file
            log_files.append(log_filename)
            console.print(f"Log para {proc_info['name']}: {log_filename}")

        layout = Layout()

        if len(process_info) == 2:
            layout.split_row(
                Layout(name="left"),
                Layout(name="right")
            )
        else:
            layout.split_column(*[Layout(name=f"proc{i}") for i in range(len(process_info))])

        def read_output(proc_info):
            try:
                for line_bytes in iter(proc_info['process'].stdout.readline, b''):
                    if not line_bytes:
                        break

                    line_str = safe_decode_fn(line_bytes)
                    line_stripped = line_str.rstrip()

                    proc_info['output'].append(line_stripped)
                    proc_info['log_file'].write(line_str)
                    proc_info['log_file'].flush()

                    if len(proc_info['output']) > 50:
                        proc_info['output'].pop(0)
            except Exception:
                pass

        threads = []
        for proc_info in process_info:
            thread = threading.Thread(target=read_output, args=(proc_info,), daemon=True)
            thread.start()
            threads.append(thread)

        try:
            with Live(layout, console=console, refresh_per_second=4) as live:
                while any(p['process'].poll() is None for p in process_info):
                    for idx, proc_info in enumerate(process_info):
                        output_text = Text.from_ansi(
                            "".join([line + "\n" for line in proc_info['output'][-30:]])
                        )

                        status = "Running" if proc_info['process'].poll() is None else f"Exited ({proc_info['process'].returncode})"
                        status_style = "green" if proc_info['process'].poll() is None else "red"

                        panel = Panel(
                            output_text,
                            title=f"[bold]{proc_info['name']}[/bold] - [{status_style}]{status}[/{status_style}]",
                            subtitle=f"{proc_info['command']}",
                            border_style="cyan" if proc_info['process'].poll() is None else "red"
                        )

                        if len(process_info) == 2:
                            layout["left" if idx == 0 else "right"].update(panel)
                        else:
                            layout[f"proc{idx}"].update(panel)

                    time.sleep(0.25)

                time.sleep(1)

        except KeyboardInterrupt:
            console.print("\n[warning]Interrompido pelo usuário[/warning]")
            for proc_info in process_info:
                if proc_info['process'].poll() is None:
                    proc_info['process'].terminate()

        for thread in threads:
            thread.join(timeout=1)

        for proc_info in process_info:
            if 'log_file' in proc_info:
                proc_info['log_file'].close()

        console.print("\n[success]Execução finalizada[/success]")
        console.print("[info]Logs salvos em:[/info]")
        for log_file in log_files:
            console.print(f"  {log_file}")

    @staticmethod
    def cleanup_processes(processes: List[subprocess.Popen]):
        """Cleanup running processes on exit."""
        for process in processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
