import cv2
from PIL import Image, ImageTk
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
import io

# =============== CONFIGURAÇÃO VISUAL ===============
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VideoAnnotatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎞️ Anotador de Vídeo por Frames")
        self.geometry("1050x800")

        self.cap = None
        self.total_frames = 0
        self.frame_number = 0
        self.annotations = {}
        self.thumbnails = {}
        self.global_comment = ""

        # Layout principal
        self.video_label = ctk.CTkLabel(self, text="Nenhum vídeo carregado.")
        self.video_label.pack(pady=10)

        # === Info de frame atual (agora usando StringVar para garantir atualização) ===
        self.frame_var = tk.StringVar(value="Você está no frame -- / --")
        self.frame_info_label = ctk.CTkLabel(self, textvariable=self.frame_var, font=("Arial", 14))
        self.frame_info_label.pack(pady=2)

        # === Controles ===
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(pady=5)

        self.btn_open = ctk.CTkButton(control_frame, text="📂 Abrir vídeo", command=self.load_video)
        self.btn_open.grid(row=0, column=0, padx=10)

        self.btn_prev = ctk.CTkButton(control_frame, text="⬅️ Anterior", command=self.prev_frame)
        self.btn_prev.grid(row=0, column=1, padx=10)

        self.btn_next = ctk.CTkButton(control_frame, text="➡️ Próximo", command=self.next_frame)
        self.btn_next.grid(row=0, column=2, padx=10)

        # === Slider ===
        self.slider = ctk.CTkSlider(self, from_=0, to=1, number_of_steps=1, command=self.slider_changed)
        self.slider.pack(pady=10, fill="x", padx=20)

        # === Campo de anotação ===
        ctk.CTkLabel(self, text="📝 Observação para este frame:").pack(pady=5)
        self.note_text = ctk.CTkTextbox(self, height=100)
        self.note_text.pack(padx=20, fill="x")

        self.btn_save_note = ctk.CTkButton(self, text="💾 Salvar anotação", command=self.save_annotation)
        self.btn_save_note.pack(pady=5)

        # === Comentário global ===
        ctk.CTkLabel(self, text="💬 Comentário global:").pack(pady=5)
        self.global_text = ctk.CTkTextbox(self, height=120)
        self.global_text.pack(padx=20, fill="x")

        # === Exportar ===
        export_frame = ctk.CTkFrame(self)
        export_frame.pack(pady=15)
        self.btn_export_csv = ctk.CTkButton(export_frame, text="📄 Exportar CSV", command=self.export_csv)
        self.btn_export_csv.grid(row=0, column=0, padx=15)
        self.btn_export_pdf = ctk.CTkButton(export_frame, text="🧾 Exportar PDF", command=self.export_pdf)
        self.btn_export_pdf.grid(row=0, column=1, padx=15)

    # =============== FUNÇÕES PRINCIPAIS ===============
    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Vídeos", "*.mp4 *.avi *.mov")])
        if not path:
            return
        self.cap = cv2.VideoCapture(path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if self.total_frames <= 0:
            messagebox.showerror("Erro", "Não foi possível ler o vídeo.")
            return
        # ajustar slider
        self.slider.configure(to=self.total_frames - 1, number_of_steps=self.total_frames - 1)
        # mostrar primeiro frame
        self.show_frame(0)

    def show_frame(self, frame_number):
        """Exibe um frame e atualiza a interface"""
        if not self.cap:
            return

        # Auto-save do frame anterior
        try:
            prev_note = self.note_text.get("1.0", "end").strip()
            if prev_note:
                self.annotations[self.frame_number] = prev_note
        except Exception:
            # não bloquear caso textbox não exista ainda
            pass

        # Ler frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        if not ret:
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img.thumbnail((640, 360))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=imgtk, text="")
        self.video_label.image = imgtk

        # Atualiza miniatura cache (para PDF)
        thumb = img.copy()
        thumb.thumbnail((250, 250))
        self.thumbnails[frame_number] = thumb

        # Atualiza anotação visível
        self.note_text.delete("1.0", "end")
        if frame_number in self.annotations:
            self.note_text.insert("1.0", self.annotations[frame_number])

        # Atualiza label de frame atual via StringVar (garante atualização imediata)
        # +1 apenas para exibir em base 1 ao usuário (frame humano começa em 1)
        try:
            self.frame_var.set(f"Você está no frame {frame_number + 1} de {self.total_frames}")
        except Exception:
            # fallback: configure
            self.frame_info_label.configure(text=f"Você está no frame {frame_number + 1} de {self.total_frames}")

        # guarda número atual
        self.frame_number = frame_number

    def slider_changed(self, value):
        """O CTkSlider passa valores float; convertemos para int e mostramos o frame"""
        try:
            v = int(float(value))
        except Exception:
            v = int(value)
        # evita re-chamar se já estivermos nesse frame
        if v != self.frame_number:
            self.show_frame(v)

    def next_frame(self):
        if self.cap:
            new_frame = min(self.frame_number + 1, self.total_frames - 1)
            # ajustar slider e mostrar (set pode disparar o comando; chamamos show_frame para garantir)
            self.slider.set(new_frame)
            self.show_frame(new_frame)

    def prev_frame(self):
        if self.cap:
            new_frame = max(self.frame_number - 1, 0)
            self.slider.set(new_frame)
            self.show_frame(new_frame)

    def save_annotation(self):
        note = self.note_text.get("1.0", "end").strip()
        self.annotations[self.frame_number] = note
        messagebox.showinfo("Salvo", f"Anotação salva para o frame {self.frame_number}.")

    # =============== EXPORTAR RELATÓRIOS ===============
    def export_csv(self):
        if not self.annotations:
            messagebox.showwarning("Aviso", "Nenhuma anotação para exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        rows = [{"Frame": f, "Observação": n} for f, n in sorted(self.annotations.items())]
        rows.append({"Frame": "Comentário Global", "Observação": self.global_text.get("1.0", "end").strip()})
        df = pd.DataFrame(rows)
        try:
            df.to_csv(path, index=False, encoding="utf-8-sig")
            messagebox.showinfo("Exportado", "Relatório CSV criado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar CSV: {e}")

    def export_pdf(self):
        if not self.annotations:
            messagebox.showwarning("Aviso", "Nenhuma anotação para exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=16)
        frame_style = ParagraphStyle("frame", parent=styles["Normal"], alignment=TA_JUSTIFY, fontSize=12, spaceAfter=10)
        comment_style = ParagraphStyle("comment", parent=styles["Normal"], alignment=TA_CENTER, fontSize=12)

        doc = SimpleDocTemplate(path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = [Paragraph("Relatório de Anotações por Frame", title_style), Spacer(1, 12)]

        # Miniaturas e observações (reutiliza thumbnails cacheadas)
        for f, n in sorted(self.annotations.items()):
            img = self.thumbnails.get(f)
            if img:
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                buf.seek(0)
                elements.append(RLImage(buf, width=img.width, height=img.height))
            elements.append(Paragraph(f"<b>Frame {f}</b>: {n}", frame_style))

        # Comentário global
        elements.append(PageBreak())
        elements.append(Paragraph("Comentário Global", title_style))
        elements.append(Paragraph(self.global_text.get("1.0", "end"), comment_style))

        try:
            doc.build(elements)
            messagebox.showinfo("Exportado", "Relatório PDF criado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {e}")

if __name__ == "__main__":
    app = VideoAnnotatorApp()
    app.mainloop()
