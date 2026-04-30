import math
import os
from io import BytesIO
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

app = FastAPI(title="Watermark Service", version="1.0.0")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
PDF_FONT_NAME = "STSong-Light"
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return r"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>文件水印工具</title>
  <style>
    :root { color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f5f7fb; color: #1f2937; }
    .wrap { max-width: 1180px; margin: 40px auto; padding: 0 20px; }
    .layout { display: grid; grid-template-columns: 360px 1fr; gap: 20px; align-items: start; }
    .card { background: #fff; border-radius: 18px; padding: 28px; box-shadow: 0 12px 36px rgba(15, 23, 42, .10); }
    h1 { margin: 0 0 8px; font-size: 28px; }
    h2 { margin: 0 0 16px; font-size: 20px; }
    p { margin: 0 0 24px; color: #64748b; }
    label { display: flex; align-items: center; margin: 18px 0 8px; font-weight: 650; }
    input { box-sizing: border-box; width: 100%; border: 1px solid #d7dce5; border-radius: 10px; padding: 11px 12px; font-size: 15px; }
    input[type="file"] { background: #f8fafc; }
    input[type="range"] { padding: 0; border: 0; accent-color: #2563eb; cursor: pointer; }
    input[type="color"] { height: 42px; padding: 4px; cursor: pointer; }
    select { box-sizing: border-box; width: 100%; border: 1px solid #d7dce5; border-radius: 10px; padding: 11px 12px; font-size: 15px; background: #fff; }
    .controls { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 8px; }
    .control { padding: 14px; border: 1px solid #e2e8f0; border-radius: 14px; background: #fbfdff; }
    .control-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-weight: 650; }
    .value { min-width: 64px; padding: 4px 8px; border-radius: 999px; background: #eaf2ff; color: #1d4ed8; text-align: center; font-size: 13px; }
    .control-note { display: none; }
    .head-actions { display: inline-flex; align-items: center; gap: 8px; margin-left: auto; }
    .help { position: relative; display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border: 0; border-radius: 50%; background: transparent; color: #94a3b8; font-size: 12px; font-weight: 700; line-height: 1; cursor: help; flex: 0 0 auto; }
    .help::after { content: attr(data-tip); position: absolute; right: 0; top: calc(100% + 8px); width: 220px; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; color: #334155; font-size: 12px; line-height: 1.6; font-weight: 400; text-align: left; box-shadow: 0 12px 30px rgba(15, 23, 42, .12); opacity: 0; visibility: hidden; transform: translateY(-4px); transition: opacity .15s ease, transform .15s ease, visibility .15s ease; z-index: 10; pointer-events: none; }
    .help::before { content: ""; position: absolute; right: 6px; top: calc(100% + 3px); border: 6px solid transparent; border-bottom-color: #e2e8f0; opacity: 0; visibility: hidden; transition: opacity .15s ease, visibility .15s ease; z-index: 11; }
    .help:hover, .help:focus { background: #eaf2ff; color: #1d4ed8; outline: none; }
    .help:hover::after, .help:hover::before, .help:focus::after, .help:focus::before { opacity: 1; visibility: visible; transform: translateY(0); }
    .minor-button { margin-top: 12px; background: #e2e8f0; color: #334155; }
    button, .download { margin-top: 24px; width: 100%; border: 0; border-radius: 12px; background: #2563eb; color: #fff; padding: 13px 18px; font-size: 16px; font-weight: 700; cursor: pointer; text-align: center; text-decoration: none; box-sizing: border-box; display: block; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .download { display: none; background: #16a34a; }
    .msg { margin-top: 16px; min-height: 22px; color: #475569; }
    .hint { margin-top: 20px; padding: 14px 16px; background: #f8fafc; border-radius: 12px; color: #64748b; font-size: 14px; line-height: 1.7; }
    .privacy-note { margin: 0 0 18px; padding: 14px 18px; border: 1px solid #bfdbfe; border-left: 5px solid #2563eb; border-radius: 14px; background: #eff6ff; color: #1e3a8a; font-size: 14px; line-height: 1.7; box-shadow: 0 8px 24px rgba(37, 99, 235, .08); }
    .preview-box { min-height: 520px; border: 1px dashed #cbd5e1; border-radius: 14px; background: #f8fafc; display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; }
    .preview-box.empty { color: #94a3b8; }
    .preview-box img { max-width: 100%; max-height: 720px; display: block; }
    .preview-box iframe { width: 100%; height: 720px; border: 0; background: #fff; }
    .position-marker { position: absolute; left: 88%; top: 88%; transform: translate(-50%, -50%); display: none; padding: 7px 14px; border: 1px dashed #2563eb; border-radius: 999px; background: rgba(15, 23, 42, .58); color: #fff; font-weight: 800; cursor: move; user-select: none; touch-action: none; z-index: 3; white-space: nowrap; backdrop-filter: blur(4px); }
    .preview-box.positioning .position-marker { display: block; }
    .mode-note { display: none; }
    .preset-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
    .preset-button { margin: 0; padding: 9px 10px; border-radius: 10px; background: #eaf2ff; color: #1d4ed8; font-size: 13px; }
    .preset-button.active { background: #2563eb; color: #fff; }
    .angle-presets { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
    .angle-button { margin: 0; width: auto; padding: 7px 10px; border-radius: 999px; background: #eaf2ff; color: #1d4ed8; font-size: 13px; }
    .angle-button.active { background: #2563eb; color: #fff; }
    .checkbox-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; color: #64748b; font-size: 13px; }
    .checkbox-row input { width: auto; }
    .hidden { display: none !important; }
    .preview-title { margin-top: 24px; }
    @media (max-width: 900px) { .layout { grid-template-columns: 1fr; } .preview-box { min-height: 360px; } }
    @media (max-width: 640px) { .controls { grid-template-columns: 1fr; } .card { padding: 22px; } }
  </style>
</head>
<body>
  <main class="wrap">
    <div class="privacy-note">
      隐私说明：文件仅用于本次水印处理，服务端不持久化保存原文件或结果文件；预览结果只临时保存在当前浏览器页面中。
    </div>
    <form id="form" class="layout">
      <section class="card">
        <h1>文件水印工具</h1>
        <p>支持 PDF、PNG、JPG/JPEG 文件。</p>

        <label for="file">选择文件</label>
        <input id="file" name="file" type="file" accept=".pdf,.png,.jpg,.jpeg" required>

        <label for="watermark_text">水印文字</label>
        <input id="watermark_text" name="watermark_text" type="text" value="内部使用" required>

        <a id="download" class="download" href="#">下载水印文件</a>
        <div id="msg" class="msg">选择文件后会自动生成预览。</div>
      </section>

      <section class="card">
        <h2>水印参数</h2>
        <div class="control">
          <div class="control-head">
            <label for="watermark_mode">水印模式</label>
            <span class="help" tabindex="0" data-tip="PDF 固定使用平铺水印；图片可使用平铺水印或定位水印。定位水印可在预览图上拖动。">i</span>
          </div>
          <select id="watermark_mode" name="watermark_mode">
            <option value="tiled">平铺水印</option>
            <option value="positioned">定位水印（图片）</option>
          </select>
        </div>
        <input id="position_x" name="position_x" type="hidden" value="0.88">
        <input id="position_y" name="position_y" type="hidden" value="0.88">
        <input id="position_preset" name="position_preset" type="hidden" value="bottom-right">
        <div id="position_controls" class="control hidden">
          <div class="control-head">
            <label for="watermark_style">定位样式</label>
            <span class="help" tabindex="0" data-tip="轻量角标适合右下角署名式水印；简洁文字更轻，但复杂背景下可能不够明显。">i</span>
          </div>
          <select id="watermark_style" name="watermark_style">
            <option value="badge">轻量角标</option>
            <option value="text">简洁文字</option>
          </select>
          <label class="checkbox-row"><input id="auto_contrast" name="auto_contrast" type="checkbox" value="true" checked> 自动反差 <span class="help" tabindex="0" data-tip="根据水印位置附近的背景自动选择黑色或白色，让角标更容易看清。">i</span></label>
        </div>
        <div id="preset_controls" class="control hidden">
          <div class="control-head">
            <label>推荐位置</label>
            <span class="help" tabindex="0" data-tip="快速把定位水印放到图片四角。选择后仍可在预览图中拖动微调。">i</span>
          </div>
          <div class="preset-grid">
            <button class="preset-button" type="button" data-preset="top-left" data-x="0.12" data-y="0.12">左上</button>
            <button class="preset-button" type="button" data-preset="top-right" data-x="0.88" data-y="0.12">右上</button>
            <button class="preset-button" type="button" data-preset="bottom-left" data-x="0.12" data-y="0.88">左下</button>
            <button class="preset-button active" type="button" data-preset="bottom-right" data-x="0.88" data-y="0.88">右下</button>
          </div>
        </div>
        <div class="controls">
          <div class="control">
            <div class="control-head">
              <label for="opacity">透明度</label>
              <span class="head-actions">
                <span id="opacity_value" class="value">28%</span>
                <span class="help" tabindex="0" data-tip="越小越淡，越大越明显。定位角标建议保持较低透明度，减少对图片观感的影响。">i</span>
              </span>
            </div>
            <input id="opacity" name="opacity" type="range" min="0.01" max="1" step="0.01" value="0.28" data-format="percent">
          </div>

          <div class="control">
            <div class="control-head">
              <label for="angle">角度</label>
              <span class="head-actions">
                <span id="angle_value" class="value">0°</span>
                <span class="help" tabindex="0" data-tip="平铺水印常用 -30° 或 -45°；定位角标建议 0°，必要时用 ±15° 微调。">i</span>
              </span>
            </div>
            <div id="angle_presets" class="angle-presets"></div>
            <input id="angle" name="angle" type="range" min="-90" max="90" step="1" value="0" data-format="degree">
          </div>

          <div id="gap_control" class="control">
            <div class="control-head">
              <label for="gap">间距</label>
              <span class="head-actions">
                <span id="gap_value" class="value">160px</span>
                <span class="help" tabindex="0" data-tip="仅影响平铺水印。数值越小水印越密集，数值越大水印越稀疏。">i</span>
              </span>
            </div>
            <input id="gap" name="gap" type="range" min="40" max="360" step="10" value="160" data-format="px">
          </div>

          <div id="color_control" class="control hidden">
            <div class="control-head">
              <label for="color">颜色</label>
              <span class="head-actions">
                <span class="value">文字</span>
                <span class="help" tabindex="0" data-tip="关闭自动反差后生效，用于自定义定位水印文字颜色。">i</span>
              </span>
            </div>
            <input id="color" name="color" type="color" value="#000000">
          </div>

          <div class="control">
            <div class="control-head">
              <label for="font_size">字体大小</label>
              <span class="head-actions">
                <span id="font_size_value" class="value">自动</span>
                <span class="help" tabindex="0" data-tip="设为 0 表示自动按文件尺寸计算。图片角标建议使用自动字号。">i</span>
              </span>
            </div>
            <input id="font_size" name="font_size" type="range" min="0" max="96" step="2" value="0" data-format="font">
          </div>
        </div>

        <button id="reset-controls" class="minor-button" type="button">恢复默认参数</button>

        <h2 class="preview-title">效果预览</h2>
        <div id="preview" class="preview-box empty">选择文件后自动生成预览<span id="position_marker" class="position-marker">内部使用</span></div>
      </section>
    </form>
    <script>
    const form = document.getElementById('form');
    const msg = document.getElementById('msg');
    const preview = document.getElementById('preview');
    const download = document.getElementById('download');
    const resetControls = document.getElementById('reset-controls');
    const fileInput = document.getElementById('file');
    const textInput = document.getElementById('watermark_text');
    const modeInput = document.getElementById('watermark_mode');
    const gapControl = document.getElementById('gap_control');
    const colorControl = document.getElementById('color_control');
    const positionControls = document.getElementById('position_controls');
    const presetControls = document.getElementById('preset_controls');
    const styleInput = document.getElementById('watermark_style');
    const autoContrastInput = document.getElementById('auto_contrast');
    const presetInput = document.getElementById('position_preset');
    const colorInput = document.getElementById('color');
    const positionX = document.getElementById('position_x');
    const positionY = document.getElementById('position_y');
    const positionMarker = document.getElementById('position_marker');
    const angleInput = document.getElementById('angle');
    const anglePresets = document.getElementById('angle_presets');
    const angleOptions = {
      tiled: [-45, -30, 0, 30, 45],
      positioned: [-15, 0, 15],
    };
    const modeDefaultAngles = { tiled: '-30', positioned: '0' };
    let angleManuallyChanged = false;
    const controls = ['opacity', 'angle', 'gap', 'font_size'];
    const defaults = { opacity: '0.28', angle: '0', gap: '160', font_size: '0' };
    let currentUrl = '';
    let previewTimer = 0;
    let requestSeq = 0;

    controls.forEach((id) => {
      const input = document.getElementById(id);
      input.addEventListener('input', () => {
        if (id === 'angle') angleManuallyChanged = true;
        updateValue(id);
        updateAnglePresetButtons();
        updatePositionMarker();
        schedulePreview();
      });
      updateValue(id);
    });

    fileInput.addEventListener('change', () => {
      updateModeState();
      schedulePreview();
    });
    textInput.addEventListener('input', () => {
      updatePositionMarker();
      schedulePreview();
    });
    modeInput.addEventListener('change', () => {
      if (!angleManuallyChanged) {
        angleInput.value = modeDefaultAngles[modeInput.value] || '0';
        updateValue('angle');
      }
      renderAnglePresets();
      updateModeState();
      schedulePreview();
    });
    colorInput.addEventListener('input', () => {
      updatePositionMarker();
      schedulePreview();
    });
    styleInput.addEventListener('change', () => {
      updatePositionMarker();
      schedulePreview();
    });
    autoContrastInput.addEventListener('change', () => {
      updateModeState(false);
      schedulePreview();
    });
    document.querySelectorAll('.preset-button').forEach((button) => {
      button.addEventListener('click', () => {
        positionX.value = button.dataset.x;
        positionY.value = button.dataset.y;
        presetInput.value = button.dataset.preset;
        updatePresetButtons();
        updatePositionMarker();
        schedulePreview();
      });
    });

    resetControls.addEventListener('click', () => {
      controls.forEach((id) => {
        document.getElementById(id).value = id === 'angle' ? modeDefaultAngles[modeInput.value] || defaults[id] : defaults[id];
        updateValue(id);
      });
      angleManuallyChanged = false;
      positionX.value = '0.88';
      positionY.value = '0.88';
      presetInput.value = 'bottom-right';
      styleInput.value = 'badge';
      autoContrastInput.checked = true;
      updatePresetButtons();
      updateModeState();
    });

    updateModeState();
    renderAnglePresets();
    setupPositionDragging();

    form.addEventListener('submit', (event) => event.preventDefault());

    function schedulePreview() {
      window.clearTimeout(previewTimer);
      previewTimer = window.setTimeout(generatePreview, 450);
    }

    async function generatePreview() {
      if (!fileInput.files.length) {
        resetPreview('选择文件后自动生成预览');
        msg.textContent = '选择文件后会自动生成预览。';
        return;
      }
      if (!textInput.value.trim()) {
        resetPreview('请输入水印文字');
        msg.textContent = '请输入水印文字。';
        return;
      }

      const seq = ++requestSeq;
      resetPreview('正在生成预览...');
      msg.textContent = '正在生成预览，请稍候...';

      const data = new FormData(form);
      if (data.get('font_size') === '0') data.delete('font_size');

      try {
        const response = await fetch('/watermark', { method: 'POST', body: data });
        if (seq !== requestSeq) return;
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.detail || '处理失败');
        }

        const blob = await response.blob();
        const disposition = response.headers.get('Content-Disposition') || '';
        const filename = getFilename(disposition) || 'watermarked_file';
        currentUrl = URL.createObjectURL(blob);

        renderPreview(blob.type, currentUrl);
        download.href = currentUrl;
        download.download = filename;
        download.style.display = 'block';
        msg.textContent = '预览已更新，确认效果后可下载。';
      } catch (error) {
        if (seq !== requestSeq) return;
        resetPreview('生成预览失败');
        msg.textContent = error.message;
      }
    }

    function renderPreview(type, url) {
      preview.classList.remove('empty');
      preview.innerHTML = '';
      if (type === 'application/pdf') {
        preview.classList.remove('positioning');
        const frame = document.createElement('iframe');
        frame.src = url;
        preview.appendChild(frame);
        return;
      }
      const image = document.createElement('img');
      image.src = url;
      image.alt = '水印预览';
      preview.appendChild(image);
      preview.appendChild(positionMarker);
      updateModeState(false);
      image.addEventListener('load', updatePositionMarker);
    }

    function resetPreview(message = '选择文件后自动生成预览') {
      if (currentUrl) URL.revokeObjectURL(currentUrl);
      currentUrl = '';
      download.removeAttribute('href');
      download.removeAttribute('download');
      download.style.display = 'none';
      preview.classList.remove('positioning');
      preview.classList.add('empty');
      preview.textContent = message;
      preview.appendChild(positionMarker);
    }

    function updateValue(id) {
      const input = document.getElementById(id);
      const output = document.getElementById(`${id}_value`);
      if (input.dataset.format === 'percent') {
        output.textContent = `${Math.round(Number(input.value) * 100)}%`;
        return;
      }
      if (input.dataset.format === 'degree') {
        output.textContent = `${input.value}°`;
        return;
      }
      if (input.dataset.format === 'px') {
        output.textContent = `${input.value}px`;
        return;
      }
      output.textContent = Number(input.value) === 0 ? '自动' : `${input.value}px`;
    }

    function renderAnglePresets() {
      const positioned = modeInput.value === 'positioned';
      const values = positioned ? angleOptions.positioned : angleOptions.tiled;
      anglePresets.innerHTML = '';
      values.forEach((value) => {
        const button = document.createElement('button');
        button.className = 'angle-button';
        button.type = 'button';
        button.dataset.angle = String(value);
        button.textContent = `${value}°`;
        button.addEventListener('click', () => {
          angleInput.value = String(value);
          angleManuallyChanged = true;
          updateValue('angle');
          updateAnglePresetButtons();
          updatePositionMarker();
          schedulePreview();
        });
        anglePresets.appendChild(button);
      });
      updateAnglePresetButtons();
    }

    function updateAnglePresetButtons() {
      document.querySelectorAll('.angle-button').forEach((button) => {
        button.classList.toggle('active', Number(button.dataset.angle) === Number(angleInput.value));
      });
    }

    function updateModeState(shouldSchedule = true) {
      const file = fileInput.files[0];
      const isImage = file ? /\.(png|jpe?g)$/i.test(file.name) : true;
      if (!isImage && modeInput.value === 'positioned') {
        modeInput.value = 'tiled';
      }
      modeInput.querySelector('option[value="positioned"]').disabled = !isImage;
      const positioned = isImage && modeInput.value === 'positioned';
      gapControl.classList.toggle('hidden', positioned);
      colorControl.classList.toggle('hidden', !positioned || autoContrastInput.checked);
      positionControls.classList.toggle('hidden', !positioned);
      presetControls.classList.toggle('hidden', !positioned);
      preview.classList.toggle('positioning', positioned && Boolean(preview.querySelector('img')));
      updatePresetButtons();
      updateAnglePresetButtons();
      updatePositionMarker();
      if (shouldSchedule) schedulePreview();
    }

    function updatePositionMarker() {
      positionMarker.textContent = textInput.value.trim() || '水印';
      positionMarker.style.color = autoContrastInput.checked ? '#ffffff' : colorInput.value;
      positionMarker.style.background = styleInput.value === 'badge' ? 'rgba(15, 23, 42, .58)' : 'transparent';
      positionMarker.style.borderColor = styleInput.value === 'badge' ? '#2563eb' : 'rgba(37, 99, 235, .45)';
      positionMarker.style.borderRadius = styleInput.value === 'badge' ? '999px' : '8px';
      positionMarker.style.transform = `translate(-50%, -50%) rotate(${document.getElementById('angle').value}deg)`;
      const image = preview.querySelector('img');
      if (!image) {
        positionMarker.style.left = `${Number(positionX.value) * 100}%`;
        positionMarker.style.top = `${Number(positionY.value) * 100}%`;
        return;
      }
      const previewRect = preview.getBoundingClientRect();
      const imageRect = image.getBoundingClientRect();
      const left = imageRect.left - previewRect.left + Number(positionX.value) * imageRect.width;
      const top = imageRect.top - previewRect.top + Number(positionY.value) * imageRect.height;
      positionMarker.style.left = `${left}px`;
      positionMarker.style.top = `${top}px`;
    }

    function updatePresetButtons() {
      document.querySelectorAll('.preset-button').forEach((button) => {
        button.classList.toggle('active', button.dataset.preset === presetInput.value);
      });
    }

    function setupPositionDragging() {
      let dragging = false;

      positionMarker.addEventListener('pointerdown', (event) => {
        if (modeInput.value !== 'positioned') return;
        dragging = true;
        positionMarker.setPointerCapture(event.pointerId);
        event.preventDefault();
      });

      positionMarker.addEventListener('pointermove', (event) => {
        if (!dragging) return;
        setPositionFromPointer(event);
      });

      positionMarker.addEventListener('pointerup', (event) => {
        if (!dragging) return;
        dragging = false;
        positionMarker.releasePointerCapture(event.pointerId);
        setPositionFromPointer(event);
        schedulePreview();
      });
    }

    function setPositionFromPointer(event) {
      const image = preview.querySelector('img');
      if (!image) return;
      const rect = image.getBoundingClientRect();
      const x = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
      const y = Math.min(Math.max((event.clientY - rect.top) / rect.height, 0), 1);
      positionX.value = x.toFixed(4);
      positionY.value = y.toFixed(4);
      presetInput.value = 'custom';
      updatePresetButtons();
      updatePositionMarker();
    }
    function getFilename(disposition) {
      const utf8 = disposition.match(/filename\*=UTF-8''([^;]+)/);
      if (utf8) return decodeURIComponent(utf8[1]);
      const ascii = disposition.match(/filename="?([^";]+)"?/);
      return ascii ? ascii[1] : '';
    }
  </script>
  </main>
</body>
</html>
"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/watermark")
async def watermark(
    file: UploadFile = File(...),
    watermark_text: str = Form(...),
    opacity: float = Form(0.18),
    angle: float = Form(-30),
    font_size: int | None = Form(None),
    gap: int = Form(160),
    watermark_mode: str = Form("tiled"),
    position_x: float = Form(0.88),
    position_y: float = Form(0.88),
    color: str = Form("#000000"),
    watermark_style: str = Form("badge"),
    position_preset: str = Form("custom"),
    auto_contrast: bool = Form(True),
) -> StreamingResponse:
    text = watermark_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="watermark_text cannot be empty")

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, PNG, JPG and JPEG files are supported")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File is larger than {MAX_UPLOAD_MB} MB")

    safe_opacity = min(max(opacity, 0.01), 1.0)
    safe_gap = max(gap, 40)

    if suffix == ".pdf":
        output = add_pdf_watermark(content, text, safe_opacity, angle, font_size, safe_gap)
        media_type = "application/pdf"
        output_name = build_output_filename(file.filename, ".pdf")
    else:
        image_format = "PNG" if suffix == ".png" else "JPEG"
        output = add_image_watermark(
            content,
            text,
            safe_opacity,
            angle,
            font_size,
            safe_gap,
            image_format,
            watermark_mode,
            position_x,
            position_y,
            color,
            watermark_style,
            position_preset,
            auto_contrast,
        )
        media_type = "image/png" if image_format == "PNG" else "image/jpeg"
        output_name = build_output_filename(file.filename, suffix)

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={"Content-Disposition": build_content_disposition(output_name)},
    )


def add_pdf_watermark(
    content: bytes,
    text: str,
    opacity: float,
    angle: float,
    font_size: int | None,
    gap: int,
) -> BytesIO:
    try:
        reader = PdfReader(BytesIO(content))
        writer = PdfWriter()

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            overlay = create_pdf_overlay(width, height, text, opacity, angle, font_size, gap)
            overlay_page = PdfReader(overlay).pages[0]
            page.merge_page(overlay_page)
            writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or unsupported PDF file") from exc


def create_pdf_overlay(
    width: float,
    height: float,
    text: str,
    opacity: float,
    angle: float,
    font_size: int | None,
    gap: int,
) -> BytesIO:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(width, height))
    size = font_size or max(24, int(min(width, height) / 16))
    pdf.setFont(load_pdf_font(), size)
    pdf.setFillColor(Color(0, 0, 0, alpha=opacity))

    diagonal = math.hypot(width, height)
    step = gap + size * max(len(text), 4) * 0.35
    start = -diagonal
    end = diagonal * 2

    x = start
    while x < end:
        y = start
        while y < end:
            pdf.saveState()
            pdf.translate(x, y)
            pdf.rotate(angle)
            pdf.drawString(0, 0, text)
            pdf.restoreState()
            y += step
        x += step

    pdf.save()
    output.seek(0)
    return output


def add_image_watermark(
    content: bytes,
    text: str,
    opacity: float,
    angle: float,
    font_size: int | None,
    gap: int,
    image_format: Literal["PNG", "JPEG"],
    watermark_mode: str,
    position_x: float,
    position_y: float,
    color: str,
    watermark_style: str,
    position_preset: str,
    auto_contrast: bool,
) -> BytesIO:
    if watermark_mode == "positioned":
        return add_positioned_image_watermark(
            content,
            text,
            opacity,
            angle,
            font_size,
            image_format,
            position_x,
            position_y,
            color,
            watermark_style,
            position_preset,
            auto_contrast,
        )
    return add_tiled_image_watermark(content, text, opacity, angle, font_size, gap, image_format)


def add_tiled_image_watermark(
    content: bytes,
    text: str,
    opacity: float,
    angle: float,
    font_size: int | None,
    gap: int,
    image_format: Literal["PNG", "JPEG"],
) -> BytesIO:
    try:
        image = Image.open(BytesIO(content))
        base = image.convert("RGBA")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or unsupported image file") from exc

    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    text_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)
    font = load_image_font(font_size or max(24, min(base.size) // 18))
    alpha = int(255 * opacity)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    step_x = max(text_width + gap, 80)
    step_y = max(text_height + gap, 80)

    for x in range(-base.width, base.width * 2, step_x):
        for y in range(-base.height, base.height * 2, step_y):
            draw.text((x, y), text, fill=(0, 0, 0, alpha), font=font)

    rotated = text_layer.rotate(angle, expand=False, resample=Image.Resampling.BICUBIC)
    overlay.alpha_composite(rotated)
    result = Image.alpha_composite(base, overlay)

    output = BytesIO()
    if image_format == "JPEG":
        result.convert("RGB").save(output, format=image_format, quality=95)
    else:
        result.save(output, format=image_format)
    output.seek(0)
    return output


def add_positioned_image_watermark(
    content: bytes,
    text: str,
    opacity: float,
    angle: float,
    font_size: int | None,
    image_format: Literal["PNG", "JPEG"],
    position_x: float,
    position_y: float,
    color: str,
    watermark_style: str,
    position_preset: str,
    auto_contrast: bool,
) -> BytesIO:
    try:
        image = Image.open(BytesIO(content))
        base = image.convert("RGBA")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or unsupported image file") from exc

    font = load_image_font(font_size or max(18, min(base.size) // 24))
    label = create_positioned_label(text, font, opacity, color, watermark_style, auto_contrast, base, position_x, position_y, position_preset)
    rotation = 0 if abs(angle + 30) < 0.001 else angle
    rotated = label.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
    left, top = resolve_position(base.size, rotated.size, position_x, position_y, position_preset)

    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    overlay.paste(rotated, (left, top), rotated)
    result = Image.alpha_composite(base, overlay)

    output = BytesIO()
    if image_format == "JPEG":
        result.convert("RGB").save(output, format=image_format, quality=95)
    else:
        result.save(output, format=image_format)
    output.seek(0)
    return output


def create_positioned_label(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    opacity: float,
    color: str,
    watermark_style: str,
    auto_contrast: bool,
    base: Image.Image,
    position_x: float,
    position_y: float,
    position_preset: str,
) -> Image.Image:
    measure = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    measure_draw = ImageDraw.Draw(measure)
    bbox = measure_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    padding_x = max(12, text_height // 2)
    padding_y = max(8, text_height // 3)
    is_badge = watermark_style != "text"

    width = text_width + padding_x * 2 if is_badge else text_width + 8
    height = text_height + padding_y * 2 if is_badge else text_height + 8
    sample_left, sample_top = resolve_position(base.size, (width, height), position_x, position_y, position_preset)
    luminance = average_luminance(base, sample_left, sample_top, width, height)

    if auto_contrast:
        if is_badge:
            text_rgb = (255, 255, 255) if luminance >= 128 else (15, 23, 42)
            badge_rgb = (15, 23, 42) if luminance >= 128 else (255, 255, 255)
        else:
            text_rgb = (15, 23, 42) if luminance >= 128 else (255, 255, 255)
            badge_rgb = None
    else:
        text_rgb = parse_hex_color(color)
        badge_rgb = (255, 255, 255) if average_color_luminance(text_rgb) < 128 else (15, 23, 42)

    label = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(label)
    if is_badge and badge_rgb:
        badge_alpha = int(170 * opacity)
        radius = max(8, height // 2)
        draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=radius, fill=(*badge_rgb, badge_alpha))

    text_alpha = int(255 * min(max(opacity + 0.35 if is_badge else opacity, 0.01), 1.0))
    text_x = padding_x - bbox[0] if is_badge else 4 - bbox[0]
    text_y = padding_y - bbox[1] if is_badge else 4 - bbox[1]
    draw.text((text_x, text_y), text, fill=(*text_rgb, text_alpha), font=font)
    return label


def resolve_position(
    image_size: tuple[int, int],
    label_size: tuple[int, int],
    position_x: float,
    position_y: float,
    position_preset: str,
) -> tuple[int, int]:
    image_width, image_height = image_size
    label_width, label_height = label_size
    margin = max(12, int(min(image_size) * 0.04))
    preset = position_preset if position_preset in {"top-left", "top-right", "bottom-left", "bottom-right"} else "custom"

    if preset == "top-left":
        left, top = margin, margin
    elif preset == "top-right":
        left, top = image_width - label_width - margin, margin
    elif preset == "bottom-left":
        left, top = margin, image_height - label_height - margin
    elif preset == "bottom-right":
        left, top = image_width - label_width - margin, image_height - label_height - margin
    else:
        left = int(clamp(position_x, 0.0, 1.0) * image_width - label_width / 2)
        top = int(clamp(position_y, 0.0, 1.0) * image_height - label_height / 2)

    max_left = max(margin, image_width - label_width - margin)
    max_top = max(margin, image_height - label_height - margin)
    return int(clamp(left, margin, max_left)), int(clamp(top, margin, max_top))


def average_luminance(image: Image.Image, left: int, top: int, width: int, height: int) -> float:
    right = min(image.width, max(left + width, left + 1))
    bottom = min(image.height, max(top + height, top + 1))
    crop = image.crop((max(left, 0), max(top, 0), right, bottom)).convert("RGB")
    pixels = list(crop.getdata())
    if not pixels:
        return 255
    return sum(average_color_luminance(pixel) for pixel in pixels) / len(pixels)


def average_color_luminance(rgb: tuple[int, int, int]) -> float:
    red, green, blue = rgb
    return 0.299 * red + 0.587 * green + 0.114 * blue


def parse_hex_color(value: str) -> tuple[int, int, int]:
    color = value.strip().lstrip("#")
    if len(color) == 3:
        color = "".join(char * 2 for char in color)
    if len(color) != 6:
        return (0, 0, 0)
    try:
        return tuple(int(color[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError:
        return (0, 0, 0)


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def load_pdf_font() -> str:
    try:
        pdfmetrics.getFont(PDF_FONT_NAME)
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT_NAME))
    return PDF_FONT_NAME


def load_image_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = find_font_path()
    if font_path:
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def find_font_path() -> str | None:
    configured_path = os.getenv("WATERMARK_FONT_PATH")
    candidates = [configured_path] if configured_path else []
    candidates.extend(FONT_CANDIDATES)

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def build_output_filename(filename: str | None, suffix: str) -> str:
    stem = Path(filename or "output").stem or "output"
    return f"{stem}_watermarked{suffix}"


def build_content_disposition(filename: str) -> str:
    fallback = "watermarked" + Path(filename).suffix
    return f"attachment; filename={fallback}; filename*=UTF-8''{quote(filename)}"
