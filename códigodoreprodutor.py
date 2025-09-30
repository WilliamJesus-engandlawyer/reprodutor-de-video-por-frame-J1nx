import streamlit as st
import cv2
import subprocess
import tempfile
import os
import pandas as pd
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.title("Reprodutor de Vídeo por Frames com Anotações e Relatório (CSV + PDF)")

# --- Funções de vídeo ---
def is_ffmpeg_available():
    try:
        proc = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.returncode == 0
    except FileNotFoundError:
        return False

def fix_video_with_ffmpeg(input_path):
    fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    cmd = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", "-movflags", "faststart", out_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (proc.returncode == 0, out_path, proc.stderr.decode("utf-8"))

def open_capture(path):
    if hasattr(cv2, "CAP_FFMPEG"):
        cap = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(path)
    return cap

def accurate_frame_count(path):
    cap = open_capture(path)
    count = 0
    with st.spinner("Contando frames com precisão (pode levar algum tempo)..."):
        while True:
            ret, _ = cap.read()
            if not ret:
                break
            count += 1
    cap.release()
    return count

# --- Upload do vídeo ---
uploaded = st.file_uploader("Escolha um vídeo", type=["mp4", "avi", "mov"])
if uploaded is not None:
    fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(uploaded.name)[1] or ".mp4")
    os.close(fd)
    with open(temp_path, "wb") as f:
        f.write(uploaded.read())

    # Abrir captura e contar frames
    cap = open_capture(temp_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        st.warning("⚠️ Contagem de frames não confiável. Tentando corrigir com ffmpeg...")
        cap.release()
        if not is_ffmpeg_available():
            st.error("❌ ffmpeg não encontrado no PATH.")
        else:
            success, fixed_path, ffmpeg_err = fix_video_with_ffmpeg(temp_path)
            if not success:
                st.error("❌ ffmpeg falhou. Últimas linhas de erro:")
                st.text("\n".join(ffmpeg_err.splitlines()[-10:]))
                total_frames = accurate_frame_count(temp_path)
            else:
                cap = open_capture(fixed_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total_frames <= 0:
                    st.warning("Contagem ainda não confiável. Fazendo leitura frame a frame...")
                    cap.release()
                    total_frames = accurate_frame_count(fixed_path)
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                temp_path = fixed_path

    if total_frames <= 0:
        st.error("❌ Não foi possível obter a contagem de frames.")
    else:
        st.success(f"✅ Vídeo carregado com {total_frames} frames detectados.")

        # --- Inicializar session_state ---
        if "frame_number" not in st.session_state:
            st.session_state.frame_number = 0
        if "annotations" not in st.session_state:
            st.session_state.annotations = {}
        if "global_comment" not in st.session_state:
            st.session_state.global_comment = ""

        # --- Slider e navegação ---
        st.session_state.frame_number = st.slider(
            "Escolha o frame",
            0, max(total_frames - 1, 0),
            st.session_state.frame_number
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Frame anterior"):
                st.session_state.frame_number = max(st.session_state.frame_number - 1, 0)
        with col2:
            if st.button("Próximo frame"):
                st.session_state.frame_number = min(st.session_state.frame_number + 1, total_frames - 1)

        # --- Mostrar frame usando buffer (evita erro ) ---
        cap.set(cv2.CAP_PROP_POS_FRAMES, st.session_state.frame_number)
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame)
            buf = io.BytesIO()
            img_pil.save(buf, format="JPEG")
            buf.seek(0)
            st.image(buf, caption=f"Frame {st.session_state.frame_number}")
        else:
            st.warning("Não foi possível carregar este frame.")

        # --- Anotação por frame ---
        note = st.text_area(
            "Anotar observação para este frame",
            value=st.session_state.annotations.get(st.session_state.frame_number, ""),
            height=100
        )
        if st.button("Salvar anotação"):
            st.session_state.annotations[st.session_state.frame_number] = note
            st.success(f"✅ Anotação salva para o frame {st.session_state.frame_number}")

        # --- Comentário global ---
        st.subheader("Comentário global sobre o desempenho do modelo")
        st.session_state.global_comment = st.text_area(
            "Escreva aqui suas considerações gerais:",
            value=st.session_state.global_comment,
            height=150
        )

        # --- Mostrar anotações ---
        if st.session_state.annotations:
            st.subheader("📋 Anotações por frame")
            df = pd.DataFrame(
                [{"Frame": f, "Observação": n} for f, n in sorted(st.session_state.annotations.items())]
            )
            st.table(df)

            # --- Exportar CSV ---
            export_rows = [{"Frame": f, "Observação": n} for f, n in sorted(st.session_state.annotations.items())]
            export_rows.append({"Frame": "Comentário Global", "Observação": st.session_state.global_comment})
            export_df = pd.DataFrame(export_rows)
            csv = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar relatório CSV",
                data=csv,
                file_name="relatorio_frames.csv",
                mime="text/csv"
            )

            # --- Exportar PDF ---
            pdf_fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
            os.close(pdf_fd)
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            c.setFont("Helvetica", 12)
            y_position = height - 50

            c.drawString(50, y_position, "Relatório de Anotações por Frame")
            y_position -= 30

            for f, n in sorted(st.session_state.annotations.items()):
                # colocar frame como miniatura
                cap.set(cv2.CAP_PROP_POS_FRAMES, f)
                ret, frame_img = cap.read()
                if ret:
                    frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_img)
                    pil_img.thumbnail((150, 150))
                    img_buf = io.BytesIO()
                    pil_img.save(img_buf, format="JPEG")
                    img_buf.seek(0)
                    c.drawImage(ImageReader(img_buf), 50, y_position-150)
                c.drawString(220, y_position-10, f"Frame {f}: {n}")
                y_position -= 170
                if y_position < 100:
                    c.showPage()
                    y_position = height - 50

            # Comentário global
            c.showPage()
            c.drawString(50, height - 50, "Comentário Global:")
            text = st.session_state.global_comment
            text_lines = text.split("\n")
            y = height - 80
            for line in text_lines:
                c.drawString(50, y, line)
                y -= 20

            c.save()

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Baixar relatório PDF",
                data=pdf_bytes,
                file_name="relatorio_frames.pdf",
                mime="application/pdf"
            )

        cap.release()




#⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⡀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⠇⠀⢠⠡⡻⢨⢣⠎⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⢀⡇⠐⣠⢳⢃⡯⢯⡜⠀⢰⣒⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠁⡜⠀⢷⠈⢱⢊⡞⣜⡻⡴⢃⠾⣸⢏⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⢀⠀⢀⡀⠐⢈⠅⣸⢨⢼⣸⡛⣼⢙⡴⢉⠲⢋⠞⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢢⠡⣆⢤⢤⡉⠐⢄⠐⢨⣾⣗⢕⣡⡎⠔⠉⠀⠦⠘⣀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠫⠟⠯⠷⠻⠿⣶⣁⠸⡧⣪⡿⠋⠠⡄⠀⠂⠐⠒⡈⢢⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⢂⡠⠤⠀⠄⠈⠀⣒⣥⣦⠻⣿⣿⣷⡄⠄⡀⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⣐⡄⢴⣷⣿⣿⣿⣿⣷⡞⢿⣿⣿⣌⠀⠁⡤⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡿⢰⣿⣿⣿⣿⣿⣿⣿⢗⠘⢙⣿⣿⠀⣜⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⢸⢳⣾⣿⣿⣿⣿⣿⣿⠏⠚⡀⣠⡯⣿⡅⢼⣿⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠀⠈⠀⠀⠀⠸⣿⣿⡿⠁⠀⠐⡈⠰⠂⣾⣿⢁⣼⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⠀⠈⠀⠀⡀⢸⣿⣀⣷⣤⡀⠀⣀⣼⣿⡏⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠃⣺⣴⣸⣿⢿⣿⣿⣿⣿⣿⣷⣿⣟⡿⠀⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⡏⢸⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡁⠀⠂⠀⠈⢿⣿⡇⢙⠿⣫⣿⣿⣿⣿⣿⠋⠀⠀⠈⡹⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠀⠀⠉⢉⣽⣿⠟⠡⠀⠀⠀⠀⢀⠁⠀⠀⠀⠀⠀⣀⣠⣤⣤⣤⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠂⣶⣶⡿⠛⠁⠀⠀⠀⠀⢀⠀⠀⢆⣖⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡶⣦⣤⠀⠂⠠⡄⠁⠄⠀⠀⠀⠀⡐⠤⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢄⣢⣦⣭⣵⣮⠇⡐⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠀⣐⣀⠠⠀⠀⠀⠠⢀⠸⡜⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⠀⢐⣴⡦⠀⠀⠁⠈⢖⠰⢀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⣀⣤⣠⣄⢠⣴⡆⣭⣭⣭⣯⣭⣿⣟⣉⣤⣴⣤⣣⢳⡴⣠⡀⠀⠀⠀⠄⡀⠠⠀⠀⠀⠠⣶⣶⡶⣶⣿⣿⡿⠀⠀⠀⠀⠁⢠⠀⣁⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⢠⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⢠⢀⡀⠔⡠⢂⠈⣶⣿⣿⣿⣿⣿⣯⣼⣷⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣏⡿⣿⣿⣷⣦⡀⠀⢷⠀⠀⠀⠀⠀⠈⠛⠙⠛⠛⠋⠀⠀⠀⠀⠠⢀⠀⢧⠨⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⢠⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⣠⢐⠶⡘⡿⢄⠈⠆⠂⠌⡐⠤⣉⢚⡛⣛⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⠻⣿⣿⡜⡳⡝⡇⣝⣻⢷⣰⡤⠀⠀⢀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠋⠂⠸⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⣾⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠛⠧⢏⡷⡁⣇⠛⠳⢈⣁⣚⣤⣥⢬⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠙⠿⡰⠡⠙⠆⠰⠽⣣⠄⠁⠀⠀⠨⡤⣤⣅⠀⠀⠀⢀⣫⡲⡆⠇⠀⠃⠀⠚⡆⣾⣿⣿⣿⣿⣿⡿⠋⠚⠉⡁⠡⠀⠄⠀⠀⠀⠀⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠲⢡⢞⠡⢁⡶⢬⠳⠚⠞⠋⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠋⠋⠉⠉⠉⠉⠉⠉⠉⠉⠛⠁⡀⠁⠢⠉⠀⢜⠛⠁⠀⠀⠀⠀⠀⠀⠈⠫⢛⣠⣶⡿⠋⠀⠀⠀⠀⠁⢀⠆⠱⢹⣿⣿⣿⣿⡟⠀⠌⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠠⡐⠤⣎⠉⠐⠉⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠁⡺⡌⠀⠀⠀⠀⠀⢀⠀⣠⣔⣾⠿⠛⢥⣶⢤⣀⡀⠀⠀⠀⠈⠠⢄⠈⣿⣿⣿⣿⣠⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠁⠈⠁⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡁⠀⠀⠀⠀⠀⢈⠤⢘⠫⠉⠀⠀⠀⠀⠈⠙⡛⠱⢄⠀⠀⠀⣀⡀⠳⠰⢻⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⡈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠂⠁⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠀⡄⠀⢽⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠄⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡐⠀⠀⠀⠀⠀⠀⠀⡀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⠀⠘⠀⠸⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⢀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠈⠐⠈⠀⠀⠁⠀⠐⠀⠀⠀⠀⠀⠀⠀⠀⠘⠀⠠⠀⠀⠀⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
