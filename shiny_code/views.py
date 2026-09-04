import os
import json
import random
import base64
from datetime import datetime
from shiny import ui
from state import AppState
from config import safe_int

# Helper membaca gambar otomatis agar tidak pernah broken
def get_image_base64(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
    except Exception:
        pass
    return f"./{filename}"

# ==============================================================================
# CSS & JAVASCRIPT ASSETS (ZERO-GLITCH, ANTI-JUMP UPLOAD & FREE SCROLL)
# ==============================================================================
CUSTOM_HEAD = ui.head_content(
    # --- 1. HTML NATIVE TITLE & FAVICON ---
    ui.tags.title("ZKN WAREHOUSE ERP"),
    ui.tags.link(rel="icon", type="image/png", href="./image_981625.png?v=99"),

    # --- 2. SCRIPT UTAMA ---
    ui.tags.script("""
        // --- 1. GEMBOK OTOMATIS JUDUL & FAVICON ---
        function setBrandTab() {
            if (document.title !== "ZKN WAREHOUSE ERP") document.title = "ZKN WAREHOUSE ERP";
            let favicon = document.querySelector("link[rel~='icon']");
            if (!favicon) {
                favicon = document.createElement('link');
                favicon.rel = 'icon';
                favicon.type = 'image/png';
                document.head.appendChild(favicon);
            }
            if (!favicon.href.includes("image_981625.png")) favicon.href = './image_981625.png?v=99';
        }
        setBrandTab();
        setInterval(setBrandTab, 1000);

        // --- 2. ENGINE PAGINASI CEPAT (0ms) ---
        window.fastTables = window.fastTables || {};
        window.renderFastTablePage = function(tableId) {
            let tState = window.fastTables[tableId];
            if (!tState) return;
            let tbody = document.getElementById(tableId + "_tbody");
            if (!tbody) return;

            let total = tState.data.length;
            let size = tState.pageSize === -1 ? total : tState.pageSize;
            let maxPages = Math.max(1, Math.ceil(total / size));
            if (tState.currentPage > maxPages) tState.currentPage = maxPages;
            if (tState.currentPage < 1) tState.currentPage = 1;

            let start = (tState.currentPage - 1) * size;
            let end = Math.min(start + size, total);

            let htmlStr = "";
            for (let i = start; i < end; i++) {
                let row = tState.data[i];
                htmlStr += "<tr>";
                for (let j = 0; j < row.length; j++) {
                    let cell = row[j] !== null && row[j] !== undefined ? String(row[j]).trim() : "";
                    if (/^-?\\d+\\.0+$/.test(cell)) cell = cell.replace(/\\.0+$/, "");
                    htmlStr += "<td>" + cell + "</td>";
                }
                htmlStr += "</tr>";
            }
            tbody.innerHTML = htmlStr;

            let info = document.getElementById(tableId + "_info");
            let pageNum = document.getElementById(tableId + "_page_num");
            let prevBtn = document.getElementById(tableId + "_prev_btn");
            let nextBtn = document.getElementById(tableId + "_next_btn");

            if (info) {
                let dispStart = total > 0 ? (start + 1) : 0;
                info.innerText = "Menampilkan " + dispStart + " - " + end + " dari " + total.toLocaleString() + " baris";
            }
            if (pageNum) pageNum.innerText = "Hal " + tState.currentPage + " / " + maxPages;
            if (prevBtn) prevBtn.disabled = (tState.currentPage <= 1);
            if (nextBtn) nextBtn.disabled = (tState.currentPage >= maxPages);
        };

        window.changeFastPageSize = function(tableId, sizeVal) {
            if (window.fastTables[tableId]) {
                window.fastTables[tableId].pageSize = parseInt(sizeVal);
                window.fastTables[tableId].currentPage = 1;
                window.renderFastTablePage(tableId);
            }
        };

        window.navFastTablePage = function(tableId, delta) {
            if (window.fastTables[tableId]) {
                window.fastTables[tableId].currentPage += delta;
                window.renderFastTablePage(tableId);
            }
        };

        // --- 3. DRAG & DROP FILE ---
        document.addEventListener('dragover', function(e) {
            let box = e.target.closest('.reflex-upload-container, .csv-batch-box');
            if (box) { e.preventDefault(); box.style.borderColor = '#E50914'; box.style.backgroundColor = '#FFF5F5'; }
        });
        document.addEventListener('dragleave', function(e) {
            let box = e.target.closest('.reflex-upload-container, .csv-batch-box');
            if (box) { e.preventDefault(); box.style.borderColor = ''; box.style.backgroundColor = ''; }
        });
        document.addEventListener('drop', function(e) {
            let box = e.target.closest('.reflex-upload-container, .csv-batch-box');
            if (box && e.dataTransfer && e.dataTransfer.files.length > 0) {
                e.preventDefault(); box.style.borderColor = ''; box.style.backgroundColor = '';
                let fileInput = box.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.files = e.dataTransfer.files;
                    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });

        // --- 4. HUMAN-AWARE ZERO-GLITCH SCROLL ENGINE ---
        let userScrollTop = 0;
        let isHumanScrolling = false;
        let humanScrollTimer = null;
        let isFileInteracting = false;

        function getContainer() {
            return document.getElementById("main-scroll-container");
        }

        // Deteksi bahwa scroll dilakukan oleh manusia asli (Wheel, Touch, Keyboard, Drag Scrollbar)
        function markHumanScroll() {
            isHumanScrolling = true;
            clearTimeout(humanScrollTimer);
            humanScrollTimer = setTimeout(function() {
                isHumanScrolling = false;
            }, 250);
        }

        window.addEventListener('wheel', markHumanScroll, { passive: true, capture: true });
        window.addEventListener('touchmove', markHumanScroll, { passive: true, capture: true });
        window.addEventListener('keydown', function(e) {
            if ([32, 33, 34, 35, 36, 38, 40].includes(e.keyCode)) markHumanScroll();
        }, { passive: true, capture: true });
        
        // Deteksi klik/drag pada scrollbar
        document.addEventListener('mousedown', function(e) {
            let c = getContainer();
            if (c) {
                let rect = c.getBoundingClientRect();
                if (e.clientX >= rect.right - 25) markHumanScroll();
            }
        }, true);
        document.addEventListener('mousemove', function(e) {
            if (e.buttons === 1) markHumanScroll();
        }, true);

        // KONTROL SCROLL: HANYA ubah userScrollTop jika manusia yang scroll.
        // Jika browser mencoba melompat ke 0 secara sepihak (glitch), tahan seketika!
        document.addEventListener('scroll', function(e) {
            let c = getContainer();
            if (!c) return;

            if (e.target === c || e.target === document) {
                if (isHumanScrolling) {
                    // Manusia sedang scroll -> simpan posisi terbarunya! (Bebas ke atas / ke bawah)
                    userScrollTop = c.scrollTop;
                } else if (userScrollTop > 0 && c.scrollTop === 0) {
                    // GLITCH BROWSER TERDETEKSI: Tiba-tiba jadi 0 tanpa ada scroll manusia!
                    // Tahan seketika di posisi semula!
                    c.scrollTop = userScrollTop;
                }
            }
        }, true);

        // KUNCI POSISI SAAT KLIK UPLOAD (Cegah lompat sebelum jendela file terbuka)
        document.addEventListener('pointerdown', function(e) {
            let c = getContainer();
            if (c && c.scrollTop > 0) {
                userScrollTop = c.scrollTop;
            }
            if (e.target && (e.target.closest('.reflex-upload-container') || e.target.closest('.btn-file') || e.target.type === 'file')) {
                isFileInteracting = true;
            }
        }, true);

        // TAHAN POSISI SAAT FILE TERPILIH DARI EXPLORER
        document.addEventListener('change', function(e) {
            if (e.target && e.target.type === 'file') {
                let c = getContainer();
                if (c && userScrollTop > 0) {
                    c.scrollTop = userScrollTop;
                    // Jaga posisi selama 350ms saat jendela explorer menutup
                    let count = 0;
                    let holdTimer = setInterval(function() {
                        if (c && c.scrollTop !== userScrollTop) c.scrollTop = userScrollTop;
                        count++;
                        if (count >= 14) {
                            clearInterval(holdTimer);
                            isFileInteracting = false;
                        }
                    }, 25);
                }
            }
        }, true);

        // CEGAH BROWSER MELEMPAR FOKUS KE ATAS SAAT INPUT FILE MENERIMA FOKUS
        window.addEventListener('focusin', function(e) {
            if (e.target && e.target.type === 'file') {
                let c = getContainer();
                if (c && userScrollTop > 0) {
                    c.scrollTop = userScrollTop;
                }
            }
        }, true);

        // --- 5. SPINNER CONTROLLER ---
        window.showGlobalSpinner = function() {
            let spinner = document.getElementById('global_reflex_loading');
            if (spinner) spinner.style.removeProperty('display');
            document.body.classList.add('process-running');
        };

        // --- 6. SHINY EVENT LISTENERS ---
        if (window.jQuery) {
            $(document).on('shiny:fileuploaded shiny:inputchanged', function() {
                let c = getContainer();
                if (c && userScrollTop > 0) {
                    c.scrollTop = userScrollTop;
                }
            });

            $(document).on('shiny:idle', function() {
                document.body.classList.remove('process-running');
                let spinner = document.getElementById('global_reflex_loading');
                if (spinner) spinner.style.removeProperty('display');
                isFileInteracting = false;
            });
        }

        // --- 7. ROUTING MENU ---
        if (window.location.pathname.endsWith('index.html') && window.history.replaceState) {
            let cleanPath = window.location.pathname.replace(/index\.html$/, '');
            window.history.replaceState(null, '', cleanPath + window.location.hash);
        }

        window.setMenuRoute = function(menuName, slug) {
            // Saat user klik menu di sidebar, reset scroll ke paling atas
            userScrollTop = 0;
            let c = getContainer();
            if (c) c.scrollTop = 0;

            try {
                let basePath = window.location.pathname.replace(/index\.html$/, '');
                if (!basePath.endsWith('/')) basePath += '/';
                if (window.history.pushState) window.history.pushState(null, '', basePath + '#' + slug);
                else window.location.hash = '#' + slug;
            } catch(e) { window.location.hash = '#' + slug; }
            Shiny.setInputValue('select_menu_item', menuName, {priority: 'event'});
        };

        window.updateUrlMenu = function(menuName) {
            let slug = menuName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            if (window.history.pushState) window.history.pushState(null, null, '#' + slug);
            else window.location.hash = '#' + slug;
        };

        document.addEventListener("DOMContentLoaded", function() {
            let h = window.location.hash.replace('#', '').trim();
            if (h) {
                setTimeout(function() { Shiny.setInputValue('initial_url_hash', h, {priority: 'event'}); }, 500);
            }
        });
    """),

    # --- 3. FONT AWESOME ICONS ---
    ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"),

    # --- 4. CSS STYLING LENGKAP ---
    ui.tags.style("""
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body, html { height: 100%; width: 100%; overflow-x: hidden; background-color: #111318; margin: 0; padding: 0; }
        
        #main-scroll-container {
            overflow-y: auto !important;
            overflow-x: hidden !important;
            scroll-behavior: auto !important;
            overscroll-behavior: contain !important;
            -webkit-overflow-scrolling: touch;
        }

        /* POSISI INPUT FILE PERSIS DI DALAM TOMBOL (CEGAH LOMPATAN SAAT DIKLIK) */
        .btn-file {
            position: relative !important;
            overflow: hidden !important;
            cursor: pointer !important;
        }
        .btn-file input[type="file"],
        .reflex-upload-container input[type="file"] {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            opacity: 0 !important;
            cursor: pointer !important;
            margin: 0 !important;
            padding: 0 !important;
            display: block !important;
            z-index: 5 !important;
        }

        .reflex-upload-container {
            border: 2px dashed #000000 !important;
            border-radius: 8px;
            background: #F8FAFC;
            padding: 1.25rem 1.5rem;
            min-height: 85px;
            width: 100%;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            position: relative !important;
            transition: border-color 0.15s ease, background-color 0.15s ease !important;
        }
        .reflex-upload-container:hover {
            border-color: #C5A059 !important;
            background-color: #FFFFFF !important;
        }
        .reflex-upload-container .shiny-input-container { margin-bottom: 0 !important; width: 100%; display: flex !important; align-items: center !important; }
        .reflex-upload-container .input-group { display: flex !important; align-items: center !important; width: 100% !important; margin-bottom: 0 !important; }
        .reflex-upload-container .input-group-prepend, .reflex-upload-container .input-group-btn { display: flex !important; align-items: center !important; margin: 0 !important; }
        .reflex-upload-container .btn-file {
            background-color: #C5A059 !important; color: white !important; font-weight: bold !important;
            border-radius: 6px !important; border: none !important; padding: 8px 18px !important;
            margin-right: 14px !important; display: inline-flex !important; align-items: center !important; height: 38px !important;
        }
        .reflex-upload-container input[type="text"].form-control {
            background-color: transparent !important; border: none !important; color: #38A169 !important;
            font-weight: 700 !important; font-size: 14px !important; box-shadow: none !important;
            padding: 0 !important; height: 38px !important; line-height: 38px !important; display: flex !important;
            align-items: center !important; width: 100% !important; flex: 1 1 auto !important;
            overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important;
        }
        .reflex-upload-container input[type="text"].form-control::placeholder { color: #718096 !important; font-weight: normal !important; font-size: 13px !important; }

        .reflex-upload-container .shiny-file-input-progress,
        .reflex-upload-container .progress,
        .csv-batch-box .shiny-file-input-progress,
        .csv-batch-box .progress { display: none !important; visibility: hidden !important; height: 0 !important; margin: 0 !important; padding: 0 !important; opacity: 0 !important; }

        .csv-batch-box {
            border: 2px dashed #000000 !important; border-radius: 12px; background: #FFF5F5;
            padding: 2rem 1.5rem; width: 100%; text-align: center; margin-bottom: 1.25rem;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .csv-batch-box .shiny-input-container { margin-bottom: 0 !important; width: 100%; }
        .csv-batch-box .input-group { display: flex !important; align-items: center !important; width: 100% !important; margin-bottom: 0 !important; }
        .csv-batch-box .btn-file { background: #1A202C !important; color: #FFFFFF !important; font-weight: 700 !important; border-radius: 6px !important; border: none !important; padding: 8px 16px !important; margin-right: 10px !important; }
        .csv-batch-box input[type="text"].form-control { background-color: transparent !important; border: none !important; color: #2D3748 !important; font-weight: 700 !important; font-size: 13px !important; box-shadow: none !important; }

        .selectize-control .selectize-input {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234A5568' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: right 0.75rem center !important;
            background-size: 14px 14px !important;
            padding-right: 2.25rem !important;
        }

        .selectize-control .selectize-input.dropdown-active {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23E50914' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='18 15 12 9 6 15'%3E%3C/polyline%3E%3C/svg%3E") !important;
        }

        select.form-control, select {
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%234A5568' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E") !important;
            background-repeat: no-repeat !important;
            background-position: right 0.75rem center !important;
            background-size: 14px 14px !important;
            padding-right: 2.25rem !important;
            -webkit-appearance: none !important;
            -moz-appearance: none !important;
            appearance: none !important;
        }

        @keyframes blinkAnimation {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.25; transform: scale(0.75); }
            100% { opacity: 1; transform: scale(1); }
        }
        .blink-online { animation: blinkAnimation 1.5s infinite ease-in-out; }

        .reflex-spinner-red {
            width: 38px; height: 38px;
            border: 3.5px solid rgba(229, 9, 20, 0.2);
            border-top-color: #E50914; border-radius: 50%;
            animation: reflexSpin 0.75s linear infinite;
        }
        @keyframes reflexSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        #global_reflex_loading { display: none; }
        body.process-running #global_reflex_loading {
            display: flex !important; position: fixed !important;
            top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important;
            background: rgba(0, 0, 0, 0.5) !important; z-index: 99990 !important;
            align-items: center !important; justify-content: center !important;
        }

        body:has(#success-modal-overlay) #global_reflex_loading,
        body:has(#error-modal-overlay) #global_reflex_loading { display: none !important; }

        #success-modal-overlay, #error-modal-overlay { z-index: 999999 !important; }

        @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 70% { transform: scale(1.15); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
        .animate-pop { animation: popIn 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
        
        #shiny-notification-panel { top: 25px !important; right: 25px !important; bottom: auto !important; left: auto !important; position: fixed !important; z-index: 999999 !important; width: 360px !important; }
        .shiny-notification { border-radius: 10px !important; box-shadow: 0 10px 25px rgba(0,0,0,0.18) !important; font-weight: 700 !important; font-size: 13px !important; padding: 14px 18px !important; margin-bottom: 10px !important; }
        .shiny-notification-message { background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important; color: #FFFFFF !important; border: none !important; }
        .shiny-notification-error { background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important; color: #FFFFFF !important; border: none !important; }
        .shiny-notification-warning { background: linear-gradient(135deg, #DD6B20 0%, #C05621 100%) !important; color: #FFFFFF !important; border: none !important; }

        .custom-clean-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        .custom-clean-table th { background: #EDF2F7; color: #1A202C; font-weight: bold; font-size: 12px; padding: 10px; white-space: nowrap; border-bottom: 1px solid #CBD5E0; }
        .custom-clean-table td { color: #2D3748; padding: 8px 10px; white-space: nowrap; border-bottom: 1px solid #EDF2F7; }
        .custom-clean-table tr:hover { background-color: #F8FAFC; }
        
        .btn-red-gradient {
            background: linear-gradient(135deg, #E50914 0%, #B20710 100%) !important;
            color: #FFFFFF !important; font-weight: 800 !important; border-radius: 6px !important;
            border: none !important; cursor: pointer; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.25);
            padding: 0.75rem 1.5rem; transition: all 0.2s ease;
        }
        .btn-red-gradient:hover { filter: brightness(1.1); }
        .btn-locked { background-color: #E50914 !important; opacity: 0.5 !important; color: white !important; font-weight: bold !important; border-radius: 6px !important; cursor: not-allowed !important; border: none !important; padding: 0.75rem 1.5rem; }

        .btn-page-nav {
            background: #FFFFFF; border: 1.5px solid #CBD5E0; border-radius: 6px;
            padding: 4px 12px; font-weight: 700; font-size: 12px; color: #1A202C;
            cursor: pointer; transition: all 0.2s ease;
        }
        .btn-page-nav:hover:not(:disabled) { background: #EDF2F7; border-color: #A0AEC0; }
        .btn-page-nav:disabled { opacity: 0.35; cursor: not-allowed; }

        details { border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 8px; background: #FFFFFF; }
        summary { font-weight: bold; padding: 10px 14px; cursor: pointer; color: #1A202C; background: #F8FAFC; border-radius: 6px; }
        details[open] summary { border-bottom: 1px solid #E2E8F0; border-radius: 6px 6px 0 0; }
        .accordion-content { padding: 14px; font-size: 13px; color: #4A5568; background: #F7FAFC; }
    """),

    # --- 5. SCRIPT LIVE TIMER ---
    ui.tags.script("""
        setInterval(function() {
            let elStore = document.getElementById('login-time-store');
            let elTimer = document.getElementById('live-timer');
            if (elStore && elTimer) {
                let loginTime = parseInt(elStore.innerText);
                if (loginTime && loginTime > 0) {
                    let now = new Date().getTime();
                    let diff = Math.floor((now - loginTime) / 1000);
                    let h = String(Math.floor(diff / 3600)).padStart(2, '0');
                    let m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
                    let s = String(diff % 60).padStart(2, '0');
                    elTimer.innerText = h + ':' + m + ':' + s;
                } else { elTimer.innerText = "00:00:00"; }
            }
        }, 1000);
    """)
)
# ==============================================================================
# MAPPING CABANG & BIN
# ==============================================================================
BRANCH_BIN_MAPPING = {
    "SURABAYA": ["GUDANG LT.2", "LIVE", "GL1-DC-KL2", "GL1-DC-KL1", "GL2-STORE", "GL2-STR", "OFFLINE", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-KL", "GL3-DC-RAK", "GL4-DC-RAK", "PUTAWAY", "KEEP AMP", "MARKOM", "DEFECT", "REJECT", "INBOUND", "BANDING"],
    "MALANG": ["GL1-BACKLINE", "GL1-C1", "GL1-C2", "GL1-C3-CTN", "GL1-C4-KL3", "GL1-KAVLING2", "DAU", "KAV2", "KAV7", "KAV8", "KAV9", "KAV10", "GL1-C0", "OFFLINE", "TOKO", "PUTAWAY", "KEEP AMP", "MARKOM", "DEFECT", "REJECT", "INBOUND", "REFUND", "BANDING"],
    "JEMBER": ["GL2-JBR", "GUDANG", "GL2-JBR-KL1", "GL2-JBR-KL2", "GL2-JBR-CTN", "GL2-JBR-GKH", "GL2-JBR-KL3", "GL2-JBR-KOLI2", "EVENT", "GAGAL QC", "INBOUND", "PUTAWAY", "REFUND", "DEFECT", "REJECT", "OFFLINE", "TOKO", "BANDING"],
    "KEDIRI": ["GL1-KDR-BACKLINE", "GL1-KDR", "GL2-KDR", "GL2-KDR-CTN", "GL3-KDR-KL1", "GL3-KDR-KL2", "GL3-KDR-KL3", "GL3-KOLI", "EVENT", "GAGAL QC", "INBOUND", "PUTAWAY", "REFUND", "DEFECT", "REJECT", "OFFLINE", "TOKO", "BANDING"],
    "SIDOARJO": ["GL2-SDA-RAK", "GL3-SDA", "GL3-SDA-BIN OFFLINE", "INBOUND", "PUTAWAY", "REFUND", "DEFECT", "REJECT", "OFFLINE", "TOKO", "BANDING", "EVENT", "GAGAL QC"],
    "SEMARANG": ["GL2-SMG", "GL2-SMG-CTN-", "GUDANG LT 2", "INBOUND", "PUTAWAY", "REFUND", "DEFECT", "REJECT", "OFFLINE", "TOKO", "BANDING", "EVENT", "GAGAL QC"],
    "HUB JAKARTA": ["GL1-JKT-A", "GL1-JKT-B", "GL1-JKT-C", "GL1-JKT-D", "GL1-JKT-E", "INBOUND", "PUTAWAY", "REFUND", "GAGAL QC", "RU HUB"],
    "ONLINE HUB SURABAYA": ["ONL","HUB","ONL-KL1","ONL-KL2"],
    "ONLINE HUB MALANG": ["HUB"]
}


# Helper membaca gambar otomatis agar tidak pernah broken/gagal load
def get_image_base64(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
    except Exception:
        pass
    return f"./{filename}"
# Helper UI Components
def metric_box(title: str, val_str: str, text_color: str, bg_gradient: str):
    return ui.div(
        ui.div(title, style="color: #4A5568; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {text_color}; font-size: 20px; font-weight: 800;"),
        style=f"background: {bg_gradient}; padding: 1rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); text-align: center; width: 100%; box-shadow: 0 2px 6px rgba(0,0,0,0.03);"
    )

def dark_metric_box(title: str, val_str: str, border_color: str):
    return ui.div(
        ui.div(title, style="color: #A0AEC0; font-size: 11px; font-weight: bold; margin-bottom: 4px;"),
        ui.div(val_str, style=f"color: {border_color}; font-size: 22px; font-weight: bold;"),
        style=f"background: #1A1A1A; padding: 1rem; border-radius: 8px; border-left: 4px solid {border_color}; width: 100%; text-align: center;"
    )

def render_clean_table(headers: list, rows: list, table_id: str = None):
    if not rows or len(rows) == 0:
        return ui.div(ui.div("Tidak ada data untuk ditampilkan.", style="color: #718096; padding: 1.5rem; font-style: italic; text-align: center;"), style="background: white; border-radius: 8px; border: 1px solid #E2E8F0; width: 100%;")
    
    if not table_id:
        table_id = f"tbl_{random.randint(100000, 999999)}"

    # Hanya render header di HTML
    th_cells = [ui.tags.th(str(h)) for h in headers]

    # Ubah data baris ke JSON (0.01 detik instan)
    json_data = json.dumps(rows)

    return ui.div(
        # --- KONTROL ATAS: FILTER BARIS DI KIRI ATAS ---
        ui.div(
            ui.div(
                ui.span("Tampilkan", style="font-size: 13px; font-weight: 700; color: #4A5568;"),
                ui.tags.select(
                    ui.tags.option("10", value="10", selected=True),
                    ui.tags.option("25", value="25"),
                    ui.tags.option("50", value="50"),
                    ui.tags.option("100", value="100"),
                    ui.tags.option("Semua", value="-1"),
                    onchange=f"window.changeFastPageSize('{table_id}', this.value)",
                    style="padding: 4px 10px; border-radius: 6px; border: 1.5px solid #CBD5E0; font-weight: 700; font-size: 12px; outline: none; background: white; cursor: pointer;"
                ),
                ui.span("baris per halaman", style="font-size: 13px; font-weight: 700; color: #4A5568;"),
                style="display: flex; align-items: center; gap: 8px;"
            ),
            style="display: flex; justify-content: flex-start; align-items: center; width: 100%; margin-bottom: 0.6rem;"
        ),

        # --- TABEL DATA (Hanya 10 baris yang dibuat oleh JS) ---
        ui.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(*th_cells)),
                ui.tags.tbody(id=f"{table_id}_tbody"),
                id=table_id,
                class_="custom-clean-table"
            ),
            style="overflow-x: auto; width: 100%; background: white; border-radius: 8px; border: 1px solid #E2E8F0;"
        ),

        # --- KONTROL BAWAH: INFO DI KIRI BAWAH, NEXT/PREV DI KANAN BAWAH ---
        ui.div(
            ui.div(
                id=f"{table_id}_info",
                style="font-size: 12px; font-weight: 600; color: #718096;"
            ),
            ui.div(
                ui.tags.button("❮ Prev", id=f"{table_id}_prev_btn", onclick=f"window.navFastTablePage('{table_id}', -1)", class_="btn-page-nav"),
                ui.span("Hal 1 / 1", id=f"{table_id}_page_num", style="font-weight: 800; font-size: 12px; color: #1A202C; padding: 0 6px;"),
                ui.tags.button("Next ❯", id=f"{table_id}_next_btn", onclick=f"window.navFastTablePage('{table_id}', 1)", class_="btn-page-nav"),
                style="display: flex; align-items: center; gap: 6px;"
            ),
            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 0.75rem; padding: 0 4px;"
        ),

        # Script render instan 10 baris pertama
        ui.tags.script(f"""
            (function() {{
                window.fastTables = window.fastTables || {{}};
                window.fastTables['{table_id}'] = {{
                    data: {json_data},
                    pageSize: 10,
                    currentPage: 1
                }};
                window.renderFastTablePage('{table_id}');
            }})();
        """),
        style="width: 100%; margin-bottom: 0.5rem;"
    )

def success_modal(show: bool):
    if not show: return ui.div()
    return ui.div(
        ui.div(
            ui.div(ui.tags.i(class_="fa-solid fa-check", style="font-size: 55px; color: white;"), class_="animate-pop", style="background: linear-gradient(135deg, #4ade80 0%, #16a34a 100%); border-radius: 50%; width: 95px; height: 95px; box-shadow: 0 10px 30px rgba(74, 222, 128, 0.5); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"),
            ui.h2("Success!", style="font-size: 32px; color: #1A202C; font-weight: 800; margin: 0;"),
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: transparent;"
        ),
        ui.tags.script("""
            document.body.classList.remove('process-running');
            setTimeout(function() {
                let el = document.getElementById('success-modal-overlay');
                if (el) { el.remove(); Shiny.setInputValue('close_success_modal_event', Math.random(), {priority: 'event'}); }
            }, 1800);
        """),
        id="success-modal-overlay",
        onclick="document.body.classList.remove('process-running'); this.remove(); Shiny.setInputValue('close_success_modal_event', Math.random(), {priority: 'event'});",
        style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; cursor: pointer;"
    )

def error_modal(show: bool, message: str = ""):
    if not show: return ui.div()
    return ui.div(
        ui.div(
            ui.div(ui.tags.i(class_="fa-solid fa-xmark", style="font-size: 55px; color: white;"), class_="animate-pop", style="background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%); border-radius: 50%; width: 95px; height: 95px; box-shadow: 0 10px 30px rgba(239, 68, 68, 0.5); margin-bottom: 10px; display: flex; align-items: center; justify-content: center;"),
            ui.h2("Gagal / Error!", style="font-size: 30px; color: #E53E3E; font-weight: 800; margin: 0 0 6px 0;"),
            ui.p(message if message else "Terjadi kesalahan saat memproses data!", style="color: #2D3748; font-size: 15px; font-weight: 700; text-align: center; max-width: 450px; margin: 0;"),
            style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: transparent;"
        ),
        ui.tags.script("""
            document.body.classList.remove('process-running');
            setTimeout(function() {
                let el = document.getElementById('error-modal-overlay');
                if (el) { el.remove(); Shiny.setInputValue('close_error_modal_event', Math.random(), {priority: 'event'}); }
            }, 2600);
        """),
        id="error-modal-overlay",
        onclick="document.body.classList.remove('process-running'); this.remove(); Shiny.setInputValue('close_error_modal_event', Math.random(), {priority: 'event'});",
        style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(5px); display: flex; align-items: center; justify-content: center; cursor: pointer;"
    )

def static_loading_spinner():
    return ui.div(
        ui.div(
            ui.div(class_="reflex-spinner-red"),
            ui.span("Sedang memproses data, mohon tunggu...", style="font-weight: bold; color: #1A202C; font-size: 14px; text-align: center;"),
            style="background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25); display: flex; flex-direction: column; align-items: center; gap: 1rem; min-width: 280px;"
        ),
        id="global_reflex_loading"
    )

# ==============================================================================
# HELPER KOMPONEN UPLOADER BOX
# ==============================================================================
def custom_uploader_box(id_str: str, title: str, placeholder: str = "200MB per file • XLSX, CSV"):
    return ui.div(
        ui.span(title, style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
        ui.div(
            ui.input_file(
                id_str, None, accept=[".xlsx", ".xls", ".csv"], multiple=False,
                button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"),
                placeholder=placeholder
            ),
            class_="reflex-upload-container"
        ),
        style="flex: 1; min-width: 260px; margin-bottom: 0.5rem;"
    )

# ==============================================================================
# VIEW 1: COMPARE SYSTEM
# ==============================================================================
def compare_system_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 1. Upload File Utama Stock System", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.div(
            custom_uploader_box("uploader_sys1", "Stock System Start Shift"),
            custom_uploader_box("uploader_sys2", "Stock System End Shift"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.h4("📤 2. Upload Dokumen Pendukung (Stok Berkurang)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.div(
            custom_uploader_box("uploader_track", "Upload Stock Tracking"),
            custom_uploader_box("uploader_rto_out", "Upload RTO OUT"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.h4("📥 3. Upload Dokumen Pendukung (Stok Bertambah)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.div(
            custom_uploader_box("uploader_po", "Upload Purchase Order (PO)"),
            custom_uploader_box("uploader_rto_in", "Upload RTO IN"),
            custom_uploader_box("uploader_refund", "Upload Mutasi REFUND"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.output_ui("compare_system_action_btn_ui"),
        style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )
    return ui.div(upload_section, ui.output_ui("compare_system_results_container"), style="width: 100%; padding: 1rem;")
    
# ==============================================================================
# VIEW 2: STOCK MINUS (BERSIH & KEMBALI KE ASLI)
# ==============================================================================
def stock_minus_view(state: AppState):
    return ui.div(
        ui.div(
            ui.span("Upload File STOCK MINUS", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
            ui.div(
                ui.input_file(
                    "upload_stock_file", None, accept=[".xlsx", ".xls"], multiple=False, 
                    button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"), 
                    placeholder="200MB per file • XLSX, XLS"
                ), 
                class_="reflex-upload-container"
            ),
            ui.output_ui("stock_minus_action_btn_ui"),
            style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),
        ui.output_ui("stock_minus_results_container"),
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# VIEW 3: PUTAWAY SYSTEM
# ==============================================================================
def putaway_view(state: AppState):
    cur_area = state.area_putaway()
    if cur_area != "":
        area_content = ui.div(
            ui.div(ui.tags.i(class_="fa-solid fa-map-pin", style="color: #3182ce; font-size: 18px; margin-right: 8px;"), ui.span("Area Terpilih: ", style="font-weight: normal; color: #2c5282; font-size: 13px;"), ui.span(cur_area, style="font-weight: bold; color: #2c5282; font-size: 13px;"), style="background: #ebf8ff; border-left: 4px solid #3182ce; padding: 10px 16px; border-radius: 6px; width: 100%; display: flex; align-items: center; margin-bottom: 1rem;"),
            ui.div(custom_uploader_box("ds_putaway_file", "Upload DS PUTAWAY"), custom_uploader_box("asal_putaway_file", "Upload ASAL BIN"), style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1rem; flex-wrap: wrap;"),
            ui.output_ui("putaway_action_btn_ui"), style="width: 100%;"
        )
    else:
        area_content = ui.div("⚠️ Silakan pilih Area Putaway di atas terlebih dahulu.", style="color: #DD6B20; font-weight: bold; font-style: italic; background: #FFFFF0; border: 1px solid #F6E05E; padding: 1rem; border-radius: 8px; width: 100%; text-align: center;")

    top_section = ui.div(
        ui.span("📍 Pilih Area Putaway", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.5rem; display: block;"),
        ui.tags.select(ui.tags.option("-- Pilih Area Putaway --", value=""), ui.tags.option("DC LANTAI 1", value="DC LANTAI 1"), ui.tags.option("DC LANTAI 2", value="DC LANTAI 2"), ui.tags.option("DC LANTAI 3", value="DC LANTAI 3"), ui.tags.option("JERSEY ZONE", value="JERSEY ZONE"), id="area_putaway_select", onchange="Shiny.setInputValue('select_area_putaway', this.value, {priority: 'event'})", style="width: 100%; padding: 10px 14px; background-color: #FFFFFF; color: #000000; font-weight: bold; font-size: 14px; border: 1.5px solid #CBD5E0; border-radius: 8px; outline: none; cursor: pointer; margin-bottom: 1rem;"),
        area_content, style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )
    return ui.div(top_section, ui.output_ui("putaway_results_container"), style="width: 100%; padding: 1rem;")

# ==============================================================================
# VIEW 4: DATABASE ONGKIR (MAIN DASHBOARD)
# ==============================================================================
def ongkir_tab2_view(state: AppState):
    selected_count = len(state.selected_ids())
    del_btn_ui = ui.tags.button(f"🗑️ HAPUS ({selected_count}) DATA", onclick="Shiny.setInputValue('btn_open_delete_modal', Math.random(), {priority: 'event'})", style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;") if selected_count > 0 else ui.div()
    
    select_options = [ui.tags.option(opt, value=opt, selected=(opt == state.filter_ekspedisi())) for opt in state.get_list_ekspedisi_options()]
    
    periode_pilihan = [
        ("SEMUA", "Semua Waktu"),
        ("HARI INI", "Hari Ini"),
        ("7 HARI TERAKHIR", "7 Hari Terakhir"),
        ("BULAN INI", "Bulan Ini"),
        ("BULAN LALU", "Bulan Lalu")
    ]
    select_periode_options = [
        ui.tags.option(label, value=val, selected=(val == state.filter_periode())) 
        for val, label in periode_pilihan
    ]

    table_rows = [
        ui.tags.tr(
            ui.tags.td(ui.tags.input(type="checkbox", checked=(str(r.get("id", "")) in set(state.selected_ids())), onchange=f"Shiny.setInputValue('toggle_row_id', '{r.get('id', '')}', {{priority: 'event'}})")),
            ui.tags.td(str(r.get("created_at", r.get("tanggal", "")))), ui.tags.td(str(r.get("supplier", ""))), ui.tags.td(str(r.get("ekspedisi", ""))),
            ui.tags.td(str(safe_int(r.get("total_koli", r.get("koli", 0))))), ui.tags.td(f"Rp {safe_int(r.get('total_ongkir', 0)):,}")
        ) for r in state.get_filtered_ongkir()
    ]

    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.span("EKSPEDISI:", style="font-size: 12px; font-weight: 800; color: #111111; margin-right: 6px;"),
                    ui.tags.select(*select_options, id="select_filter_ekspedisi", onchange="Shiny.setInputValue('change_filter_ekspedisi', this.value, {priority: 'event'})", style="background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #1A202C !important; border-radius: 8px !important; font-weight: 800 !important; width: 170px; padding: 6px 10px; cursor: pointer;"),
                    style="display: flex; align-items: center;"
                ),
                ui.div(
                    ui.span("PERIODE:", style="font-size: 12px; font-weight: 800; color: #111111; margin-left: 12px; margin-right: 6px;"),
                    ui.tags.select(*select_periode_options, id="select_filter_periode", onchange="Shiny.setInputValue('change_filter_periode', this.value, {priority: 'event'})", style="background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #1A202C !important; border-radius: 8px !important; font-weight: 800 !important; width: 170px; padding: 6px 10px; cursor: pointer;"),
                    style="display: flex; align-items: center;"
                ),
                style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px;"
            ), 
            del_btn_ui, 
            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 1.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 10px;"
        ),
        ui.div(
            metric_box("💰 BIAYA ALL", state.metric_total_biaya_all(), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            metric_box("📦 KOLI ALL", state.metric_total_koli_all(), "#1A202C", "linear-gradient(135deg, #E2E8F0 0%, #CBD5E0 100%)"),
            metric_box("📊 AVG COST ALL", state.metric_avg_cost_all(), "#C53030", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            metric_box("🚚 BIAYA DATANG", state.metric_biaya_datang(), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
            metric_box("📦 KOLI DATANG", state.metric_koli_datang(), "#276749", "linear-gradient(135deg, #C6F6D5 0%, #9AE6B4 100%)"),
            metric_box("🔄 BIAYA RTO", state.metric_biaya_rto(), "#9B2C2C", "linear-gradient(135deg, #FED7D7 0%, #FEB2B2 100%)"),
            style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
        ),
        ui.div(ui.tags.table(ui.tags.thead(ui.tags.tr(ui.tags.th("SELECT", style="text-align: center;"), ui.tags.th("TANGGAL"), ui.tags.th("SUPPLIER"), ui.tags.th("EKSPEDISI"), ui.tags.th("KOLI"), ui.tags.th("TOTAL ONGKIR")), style="background-color: #CBD5E0 !important;"), ui.tags.tbody(*table_rows) if len(table_rows) > 0 else ui.tags.tr(ui.tags.td("Tidak ada transaksi ongkir.", colspan="6", style="text-align: center; color: #718096; padding: 2rem;")), class_="custom-clean-table"), style="background: #FFFFFF; border-radius: 16px; border: 2.5px solid #1A202C; padding: 1rem; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.04); overflow-x: auto;"),
        style="width: 100%;"
    )

def main_dashboard_view(state: AppState):
    STYLE_LABEL_CSS = "font-size: 11px; font-weight: 800; color: #1A202C; margin-bottom: 2px; letter-spacing: 0.5px; display: block;"
    tab1_content = ui.div(
        ui.div(
            ui.div(ui.span("📝", style="font-size: 20px; margin-right: 8px;"), ui.h4("Input Transaksi Manual", style="font-size: 16px; font-weight: bold; color: #1A202C; margin: 0;"), style="display: flex; align-items: center; margin-bottom: 0.75rem;"),
            ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
            ui.div(ui.span("NAMA SUPPLIER", style=STYLE_LABEL_CSS), ui.tags.input(id="input_supplier", type="text", placeholder="Masukkan Nama Supplier...", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="margin-bottom: 0.75rem; width: 100%;"),
            ui.div(ui.div(ui.span("EKSPEDISI", style=STYLE_LABEL_CSS), ui.tags.input(id="input_ekspedisi", type="text", placeholder="Nama Ekspedisi...", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1; margin-right: 8px;"), ui.div(ui.span("TOTAL KOLI", style=STYLE_LABEL_CSS), ui.tags.input(id="input_koli", type="number", value="1", placeholder="Jumlah Koli", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1;"), style="display: flex; width: 100%; margin-bottom: 0.75rem;"),
            ui.div(ui.div(ui.span("TOTAL ONGKIR (RP)", style=STYLE_LABEL_CSS), ui.tags.input(id="input_ongkir", type="number", value="0", placeholder="Rp 0", style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1; margin-right: 8px;"), ui.div(ui.span("TANGGAL", style=STYLE_LABEL_CSS), ui.tags.input(id="input_tgl", type="date", value=datetime.now().strftime("%Y-%m-%d"), style="background-color: #FFFFFF; color: #111111; border: 2px solid #4A5568; border-radius: 8px; font-weight: 600; padding: 0.6rem 0.8rem; width: 100%; outline: none;"), style="flex: 1;"), style="display: flex; width: 100%; margin-bottom: 1.25rem;"),
            ui.tags.button("🚀 SIMPAN DATA ONGKIR", onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_save_ongkir_manual', {supplier: document.getElementById('input_supplier').value, ekspedisi: document.getElementById('input_ekspedisi').value, koli: document.getElementById('input_koli').value, ongkir: document.getElementById('input_ongkir').value, tgl: document.getElementById('input_tgl').value}, {priority: 'event'});", class_="btn-red-gradient", style="width: 100%; height: 48px; font-size: 14px;"),
            style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; box-shadow: 0 10px 25px rgba(0,0,0,0.03); padding: 1.8rem; flex: 1; min-width: 320px;"
        ),
        ui.div(
            ui.div(ui.span("📁", style="font-size: 20px; margin-right: 8px;"), ui.h4("Batch CSV Upload", style="font-size: 16px; font-weight: bold; color: #1A202C; margin: 0;"), style="display: flex; align-items: center; margin-bottom: 0.75rem;"),
            ui.hr(style="border-color: #CBD5E0; margin-bottom: 1rem;"),
            ui.div(ui.div(ui.span("☁️", style="font-size: 24px;"), style="padding: 10px; background: #E2E8F0; border-radius: 50%; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;"), ui.span("atau tarik & lepaskan file CSV di sini", style="font-size: 13px; color: #4A5568; font-weight: bold; margin-bottom: 10px;"), ui.input_file("upload_csv_batch", None, accept=[".csv"], multiple=False, button_label="Pilih File CSV", placeholder="Pilih file CSV..."), class_="csv-batch-box"),
            ui.tags.button("⚡ EXECUTE BATCH UPLOAD", onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_execute_batch_upload', Math.random(), {priority: 'event'});", style="background: #1A202C; color: #FFFFFF !important; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); width: 100%; height: 48px; border: none; font-size: 14px;"),
            style="background: #FFFFFF; border-radius: 16px; border: 2px solid #CBD5E0; box-shadow: 0 10px 25px rgba(0,0,0,0.03); padding: 1.8rem; flex: 1; min-width: 320px;"
        ), style="display: flex; flex-wrap: wrap; gap: 1.25rem; width: 100%; margin-top: 1.5rem;"
    )

    return ui.div(
        ui.navset_card_tab(
            ui.nav_panel("📥 INPUT & BATCH DATA", tab1_content), 
            ui.nav_panel("📊 SUMMARY & HISTORY", ui.output_ui("ongkir_tab2_dynamic_ui"))
        ), 
        style="width: 100%; background-color: #F7FAFC; min-height: 100vh; padding: 1rem;"
    )

# ==============================================================================
# VIEW 5: LIST BIN CYCLE COUNT (MENU: "List Bin Cycle Count")
# ==============================================================================
def cycle_count_view(state: AppState):
    uploader_ui = ui.div(
        ui.span("Upload File Multiple Adjustment", style="font-weight: bold; color: #1A202C; font-size: 14px; margin-bottom: 0.25rem; display: block;"),
        ui.div(
            ui.input_file(
                "upload_cycle_count_file", None, accept=[".xlsx", ".xls", ".csv"], multiple=False,
                button_label=ui.tags.span(ui.tags.i(class_="fa-solid fa-upload", style="margin-right: 6px; font-size: 14px;"), "Upload"),
                placeholder="200MB per file • XLSX, XLS, CSV"
            ),
            class_="reflex-upload-container"
        ),
        ui.output_ui("cycle_count_action_btn_ui"),
        style="width: 100%; background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )
    return ui.div(uploader_ui, ui.output_ui("cycle_count_results_container"), style="width: 100%; padding: 1rem;")

# ==============================================================================
# VIEW 6: PUTAWAY & PICKING AUDIT LIST (MENU: "Putaway & Picking Audit List")
# ==============================================================================
def ppa_audit_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 Upload Dokumen Audit (Sales, RTO, & Mutasi)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("uploader_ppa_sales", "1. File Sales (Excel / CSV)"),
            custom_uploader_box("uploader_ppa_rto", "2. File RTO (Excel / CSV)"),
            custom_uploader_box("uploader_ppa_mutasi", "3. File Mutasi (Excel / CSV)"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 1.25rem; flex-wrap: wrap;"
        ),
        ui.output_ui("ppa_action_btn_ui"),
        style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )
    return ui.div(upload_section, ui.output_ui("ppa_results_container"), style="width: 100%; padding: 1rem;")

# ==============================================================================
# VIEW 7: CYCLE COUNT ANALYZER (MENU: "Cycle Count")
# ==============================================================================
def cycle_count_analyzer_view(state: AppState):
    list_sub_kat = ["BAG", "BALL", "BASELAYER", "BOTTLE", "CLEANNING & CARE", "EXTRA SHOES", "HARDWARE", "JACKET", "JERSEY", "LOWER BODY", "NUTRITION", "OTHER", "OTHERS", "PANTS", "RACKET", "SANDALS", "SET APPAREL", "SHIRT", "SHOES", "SHORT", "SWLM", "UKNOWN SC", "UNDERLAYER", "UPPER BODY"]
    list_brand = ["MILLS", "ORTUSEIGHT", "SPECS", "ARDILES", "NINETEN", "LYCAN", "PATROBAS", "PIERO", "PORTO", "BRODO", "JACK IDN", "JOHNSON", "NOIJ", "VENTELA", "DESLE", "LEAGUE", "UNERD", "CALCI", "HUNDRED", "FIXCH", "YONEX", "NIKE", "AZA", "ASICS", "EAGLE", "PUMA", "KARGE", "GUMI", "ZUMA", "MILESTONE", "WEIDENMANN", "DIADORA", "HEIDEN HERITAGE", "LOTTO", "KRONIKEL", "ADIDAS", "VOOLA", "RECOIR", "MIZUNO", "UNKNOWN", "WARRIOR", "AVO", "KANKY"]
    list_bin_cov = ["KARANTINA", "STAGGING", "STAGING", "GUDANG LT.2", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL1", "GL4-DC-KL2", "GL3-DC-RAK", "GL4-DC-RAK", "LIVE", "MARKOM", "AMP", "GL2-STORE", "PUTAWAY", "OUT", "INB"]

    # Filter Section
    filter_section = ui.div(
        ui.div(
            ui.input_select("cca_branch", "🏢 Pilih Cabang / Branch:", choices=list(BRANCH_BIN_MAPPING.keys()), selected="SURABAYA", width="100%"),
            style="width: 100%; margin-bottom: 1rem;"
        ),
        ui.div(
            ui.div(ui.input_selectize("cca_sub_kat", "📁 Sub Kategori:", choices=list_sub_kat, multiple=True, width="100%"), style="flex: 1; min-width: 180px;"),
            ui.div(ui.input_selectize("cca_brand", "🏷️ Brand:", choices=list_brand, multiple=True, width="100%"), style="flex: 1; min-width: 180px;"),
            ui.div(ui.output_ui("cca_bin_sys_ui"), style="flex: 1; min-width: 180px;"),
            ui.div(ui.input_selectize("cca_bin_cov", "📡 BIN Coverage:", choices=list_bin_cov, multiple=True, width="100%"), style="flex: 1; min-width: 180px;"),
            style="display: flex; gap: 1rem; width: 100%; flex-wrap: wrap;"
        ),
        style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    # Step 1 Cycle Count (Kembalikan ke id cca_*)
    step1_ui = ui.div(
        ui.h4("1️⃣ Upload Data Scan & All Data Stock", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("cca_up_scan", "📥 DATA SCAN"),
            custom_uploader_box("cca_up_stock", "📥 STOCK SYSTEM"),
            style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%; margin-bottom: 0.5rem;"
        ),
        ui.output_ui("cca_step1_btn_ui"),
        ui.output_ui("cca_step1_results_ui"),
        class_="step-card-box",
        style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    return ui.div(
        filter_section,
        step1_ui,
        ui.output_ui("cca_step2_card_ui"),
        ui.output_ui("cca_step4_card_ui"),
        ui.output_ui("cca_step5_card_ui"),
        ui.output_ui("cca_step6_card_ui"),
        style="width: 100%; padding: 1rem;"
    )
    

# ==============================================================================
# VIEW COMPARE RTO (RTO GATEWAY SYSTEM)
# ==============================================================================
def compare_rto_view(state: AppState):
    # Step 1: Upload DS RTO & AppSheet RTO
    step1_ui = ui.div(
        ui.h4("1️⃣ Upload Data Scan (DS RTO) & Spreadsheet RTO", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("uploader_rto_ds", "1. DS RTO "),
            custom_uploader_box("uploader_rto_app", "2. APPSHEET RTO "),
            style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%; margin-bottom: 0.5rem;"
        ),
        ui.div(
            ui.tags.button(
                ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "JALANKAN PROSES"),
                onclick="document.body.classList.add('process-running'); Shiny.setInputValue('btn_run_rto_step1', Math.random(), {priority: 'event'});",
                class_="btn-red-gradient"
            ),
            style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
        ),
        ui.output_ui("rto_step1_results_ui"),
        style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    return ui.div(
        step1_ui,
        ui.output_ui("rto_step2_card_ui"),
        ui.output_ui("rto_step3_card_ui"),
        ui.output_ui("rto_step4_card_ui"),
        style="width: 100%; padding: 1rem;"
    )
# ==============================================================================
# VIEW STOCK OPNAME ANALYZER (LENGKAP 6 STEP)
# ==============================================================================
def stock_opname_view(state: AppState):
    list_sub_kat = ["BAG", "BALL", "BASELAYER", "BOTTLE", "CLEANNING & CARE", "EXTRA SHOES", "HARDWARE", "JACKET", "JERSEY", "LOWER BODY", "NUTRITION", "OTHER", "OTHERS", "PANTS", "RACKET", "SANDALS", "SET APPAREL", "SHIRT", "SHOES", "SHORT", "SWLM", "UKNOWN SC", "UNDERLAYER", "UPPER BODY"]
    list_bin_cov = ["KARANTINA", "STAGGING", "STAGING", "GUDANG LT.2", "TOKO", "GL1-DC", "RAK ACC LT.1", "GL3-DC-A", "GL3-DC-B", "GL3-DC-C", "GL3-DC-D", "GL3-DC-E", "GL3-DC-F", "GL3-DC-G", "GL3-DC-H", "GL3-DC-I", "GL3-DC-J", "GL4-DC-A", "GL4-DC-B", "GL4-DC-KL1", "GL4-DC-KL2", "GL3-DC-RAK", "GL4-DC-RAK", "LIVE", "MARKOM", "AMP", "GL2-STORE", "PUTAWAY", "OUT", "INB"]

    filter_section = ui.div(
        ui.div(
            ui.input_select("so_branch", "🏢 Pilih Cabang / Branch:", choices=list(BRANCH_BIN_MAPPING.keys()), selected="SURABAYA", width="100%"),
            style="width: 100%; margin-bottom: 1rem;"
        ),
        ui.div(
            ui.div(ui.input_selectize("so_sub_kat", "📁 Sub Kategori:", choices=list_sub_kat, multiple=True, width="100%"), style="flex: 1; min-width: 200px;"),
            ui.div(ui.output_ui("so_bin_sys_ui"), style="flex: 1; min-width: 200px;"),
            ui.div(ui.input_selectize("so_bin_cov", "📡 BIN Coverage (Step 2):", choices=list_bin_cov, multiple=True, width="100%"), style="flex: 1; min-width: 200px;"),
            style="display: flex; gap: 1rem; width: 100%; flex-wrap: wrap;"
        ),
        style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    # Step 1 Stock Opname (Gunakan so_step1_btn_ui agar terkunci)
    step1_ui = ui.div(
        ui.h4("1️⃣ Upload Data Scan & All Data Stock", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("so_up_scan", "📥 DATA SCAN"),
            custom_uploader_box("so_up_stock", "📥 STOCK SYSTEM"),
            style="display: flex; gap: 1rem; flex-wrap: wrap; width: 100%; margin-bottom: 0.5rem;"
        ),
        # --- TOMBOL DINAMIS TERKUNCI ---
        ui.output_ui("so_step1_btn_ui"),
        ui.output_ui("so_step1_results_ui"),
        style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

    return ui.div(
        filter_section,
        step1_ui,
        ui.output_ui("so_step2_card_ui"),
        ui.output_ui("so_step4_card_ui"),
        ui.output_ui("so_step5_card_ui"),
        ui.output_ui("so_step6_card_ui"),
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# VIEW JUSTIFICATION SO (DENGAN LOGIKA KUNCI TOMBOL OTOMATIS)
# ==============================================================================
def justification_so_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 Upload Dokumen Justifikasi Adjustment", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("uploader_jso_case", "1. File Adjustment (Plus & Minus)"),
            custom_uploader_box("uploader_jso_track", "2. Summary Stock (Dashboard Asset)"),
            custom_uploader_box("uploader_jso_all", "3. All Data Stock (Multiple Adj.)"),
            custom_uploader_box("uploader_jso_scan", "4. Data Scan (Opsional)"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
        ),
        # Ganti tombol statis dengan sub-render tombol otomatis:
        ui.output_ui("justification_so_action_btn_ui"),
        style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )

    results_ui = ui.output_ui("justification_so_results_container")

    return ui.div(
        upload_section,
        results_ui,
        style="width: 100%; padding: 1rem;"
    )


# ==============================================================================
# VIEW: CROSS CHECK REAL & SYSTEM (MATCHING KARANTINA)
# ==============================================================================
def cross_check_real_system_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 Upload Dokumen System & Real Aktual", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("uploader_crs_sys", "1. Laporan System (+)"),
            custom_uploader_box("uploader_crs_real", "2. Laporan Real (+)"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
        ),
        ui.output_ui("cross_check_action_btn_ui"),
        style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )

    results_section = ui.output_ui("cross_check_results_container")

    return ui.div(
        upload_section,
        results_section,
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# VIEW: BALANCING STOCK & DYNAMIC ALLOCATION
# ==============================================================================
def balancing_stock_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 Upload Data All Stock & Histori Penjualan (Sales)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("uploader_bs_stock", "1. File ALL DATA STOCK (Multiple Adj.)"),
            custom_uploader_box("uploader_bs_sales", "2. File SALES REPORT (90 Hari Terakhir)"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
        ),
        ui.output_ui("balancing_stock_action_btn_ui"),
        style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )

    results_section = ui.output_ui("balancing_stock_results_container")

    return ui.div(
        upload_section,
        results_section,
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# VIEW: PHYSICAL INVENTORY LIST (UNIFIED 2-IN-1 MODE)
# ==============================================================================
def physical_inventory_list_view(state: AppState):
    mode_selector = ui.div(
        ui.div(
            ui.span("🎯 PILIH METODE PENARIKAN DATA PHYSICAL INVENTORY:", style="font-weight: 800; color: #1A202C; font-size: 13px; margin-bottom: 6px; display: block; letter-spacing: 0.5px;"),
            ui.tags.select(
                ui.tags.option("-- Pilih Metode Penarikan Data Physical Inventory --", value="", selected=(state.pil_mode() == "")),
                ui.tags.option("1. TARIK BY PUTAWAY & PICKING AUDIT", value="PUTAWAY & PICKING AUDIT", selected=(state.pil_mode() == "PUTAWAY & PICKING AUDIT")),
                ui.tags.option("2. TARIK BY NON PUTAWAY &PICKING AUDIT ", value="NON AUDIT (MULTIPLE ADJ)", selected=(state.pil_mode() == "NON AUDIT (MULTIPLE ADJ)")),
                id="select_pil_mode_input",
                onchange="Shiny.setInputValue('change_pil_mode', this.value, {priority: 'event'})",
                style="width: 100%; padding: 10px 14px; background-color: #FFFFFF; color: #1A202C; font-weight: 800; font-size: 14px; border: 2px solid #CBD5E0; border-radius: 8px; outline: none; cursor: pointer;"
            ),
            style="width: 100%;"
        ),
        style="background: white; padding: 1.25rem 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);"
    )

    dynamic_body = ui.output_ui("pil_dynamic_body_ui")

    return ui.div(
        mode_selector,
        dynamic_body,
        style="width: 100%; padding: 1rem;"
    )


def menu_item(label: str, target_menu: str, current_menu: str):
    import re
    is_active = (current_menu == target_menu)
    bg_style = "background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);" if is_active else "background: transparent; color: #CBD5E0; font-weight: 500;"
    
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', target_menu).strip('-').lower()
    
    # Panggil fungsi 1 baris rapat agar browser mengeksekusinya seketika
    onclick_js = f"window.setMenuRoute('{target_menu}', '{slug}');"
    
    return ui.tags.button(
        label, 
        onclick=onclick_js, 
        style=f"width: 100%; text-align: left; padding: 0.5rem 0.75rem; margin-bottom: 3px; border-radius: 6px; font-size: 0.85rem; border: none; cursor: pointer; justify-content: flex-start; transition: all 0.2s ease; {bg_style}"
    )

def section_dropdown_header(title: str, dropdown_key: str, is_open: bool):
    icon_tag = "fa-chevron-down" if is_open else "fa-chevron-right"
    return ui.tags.div(ui.tags.span(title, style="font-size: 11px; font-weight: bold; color: #FFFFFF; letter-spacing: 0.05em;"), ui.tags.i(class_=f"fa-solid {icon_tag}", style="font-size: 12px; color: #FFFFFF;"), onclick=f"Shiny.setInputValue('toggle_dropdown_section', '{dropdown_key}', {{priority: 'event'}})", style="display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer; background: rgba(255, 255, 255, 0.05); margin-top: 0.8rem; margin-bottom: 0.3rem;")

def sidebar(state: AppState):
    cur_menu = state.main_menu()
    if not state.sidebar_open():
        return ui.div(ui.tags.button(ui.tags.i(class_="fa-solid fa-bars", style="font-size: 18px; color: #FFFFFF;"), onclick="Shiny.setInputValue('btn_toggle_sidebar', Math.random(), {priority: 'event'})", style="background: transparent; border: none; cursor: pointer; padding: 0.5rem; border-radius: 6px;"), style="width: 60px; min-width: 60px; padding: 1rem 0.5rem; background: #111318; border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column; align-items: center;")

    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-boxes-stacked", style="color: #FFFFFF; font-size: 18px;"),
                    style="""
                        width: 38px; height: 38px; 
                        background: linear-gradient(135deg, #E50914 0%, #B20710 100%); 
                        border-radius: 8px; display: flex; align-items: center; justify-content: center; 
                        box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4); flex-shrink: 0;
                    """
                ),
                ui.div(ui.span("ZKN LOGISTIC", style="color: #E50914; font-weight: 900; font-size: 14px; letter-spacing: 0.5px; line-height: 1.2;"), ui.span("WAREHOUSE SYSTEM", style="color: #FFFFFF; font-weight: 700; font-size: 10px; letter-spacing: 1.5px; opacity: 0.9;"), style="display: flex; flex-direction: column; justify-content: center;"),
                style="display: flex; align-items: center; gap: 10px;"
            ),
            ui.tags.button(ui.tags.i(class_="fa-solid fa-angles-left", style="font-size: 14px; color: #CBD5E0;"), onclick="Shiny.setInputValue('btn_toggle_sidebar', Math.random(), {priority: 'event'})", style="background: transparent; border: none; cursor: pointer; padding: 6px; border-radius: 4px; display: flex; align-items: center;"),
            style="display: flex; justify-content: space-between; width: 100%; align-items: center; margin-bottom: 0.8rem; padding-bottom: 0.6rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08);"
        ),
        ui.div(
            ui.div(section_dropdown_header("OPERATIONAL", "operational", state.dropdown_operational()), ui.div(*[menu_item(item, item, cur_menu) for item in state.get_menu_operational()], style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_operational() else "display: none;"), style="width: 100%;"),
            ui.div(section_dropdown_header("INVENTORY", "inventory", state.dropdown_inventory()), ui.div(*[menu_item(item, item, cur_menu) for item in state.get_menu_inventory()], style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_inventory() else "display: none;"), style="width: 100%;"),
            ui.div(section_dropdown_header("REJECT & DEFECT", "reject", state.dropdown_reject()), ui.div(*[menu_item(item, item, cur_menu) for item in state.get_menu_reject()], style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_reject() else "display: none;"), style="width: 100%;"),
            ui.div(section_dropdown_header("EXTRAS", "extras", state.dropdown_extras()), ui.div(*[menu_item(item, item, cur_menu) for item in state.get_menu_extras()], style="width: 100%; padding-left: 0.5rem; display: flex; flex-direction: column;" if state.dropdown_extras() else "display: none;"), style="width: 100%;"),
            style="width: 100%; flex: 1; overflow-y: auto; padding-right: 4px;"
        ),
        ui.div(ui.tags.button(ui.tags.span(ui.tags.i(class_="fa-solid fa-right-from-bracket", style="margin-right: 8px; font-size: 14px;"), ui.span("Logout Sistem", style="font-weight: bold; font-size: 13px;")), onclick="Shiny.setInputValue('btn_execute_logout', Math.random(), {priority: 'event'})", class_="btn-red-gradient", style="width: 100%; padding: 0.5rem; border-radius: 6px; display: flex; align-items: center; justify-content: center;"), style="width: 100%; padding-top: 0.8rem; border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: auto;"),
        style="width: 280px; min-width: 280px; padding: 1rem; background: linear-gradient(180deg, #111318 0%, #1A1D24 50%, #0D0F12 100%); border-right: 1px solid #2D3748; height: 100vh; display: flex; flex-direction: column; align-items: flex-start;"
    )

def login_page():
    return ui.div(
        ui.div(
            ui.div(
                ui.div(ui.div(style="width: 10px; height: 36px; background: #E50914; border-radius: 4px; margin-right: 12px;"), ui.div(ui.h2("LOGISTIC DISTRIBUTION CENTER", style="color: #FFFFFF; font-size: 20px; font-weight: 800; letter-spacing: 1px; margin: 0; line-height: 1.1;"), ui.span("PT ZONA KARYA NUSANTARA • WAREHOUSE", style="color: #E50914; font-size: 10px; font-weight: 700; letter-spacing: 2px; margin-top: 2px;"), style="display: flex; flex-direction: column;"), style="display: flex; align-items: center; margin-bottom: 0.5rem;"),
                ui.hr(style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.12); margin: 0.4rem 0 0.75rem 0;"),
                ui.p("Silakan masuk dengan akun resmi gudang Anda.", style="color: #B0B0B0; font-size: 13px; margin: 0 0 1.1rem 0;"),
                ui.div(ui.span("USERNAME", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"), ui.tags.input(id="login_username_field", type="text", placeholder="Masukkan username...", onkeydown="if (event.key === 'Enter') document.getElementById('btn_sign_in').click();", style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"), style="margin-bottom: 1rem;"),
                ui.div(ui.span("PASSWORD", style="font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px; margin-bottom: 4px; display: block;"), ui.tags.input(id="login_password_field", type="password", placeholder="Masukkan password...", onkeydown="if (event.key === 'Enter') document.getElementById('btn_sign_in').click();", style="background: rgba(0, 0, 0, 0.75); border: 1px solid rgba(229, 9, 20, 0.4); color: #FFFFFF; border-radius: 10px; padding: 0.8rem 1rem; width: 100%; outline: none;"), style="margin-bottom: 1.5rem;"),
                ui.div(style="height: 6px;"),
                ui.tags.button("SIGN IN TO SYSTEM →", id="btn_sign_in", onclick="Shiny.setInputValue('btn_submit_login', {user: document.getElementById('login_username_field').value, pass: document.getElementById('login_password_field').value}, {priority: 'event'})", class_="btn-red-gradient", style="width: 100%; height: 48px; font-size: 14px; font-weight: 800; border-radius: 10px; cursor: pointer; box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);"),
                ui.div("🟢 Warehouse Supporting Tools v2.0", style="color: #888888; font-size: 12px; text-align: center; margin-top: 10px;"),
                style="display: flex; flex-direction: column; width: 100%;"
            ),
            style="width: 100%; max-width: 520px; padding: 3rem 2.5rem; background: rgba(12, 12, 15, 0.88); backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.12); border-left: 5px solid #E50914; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);"
        ),
        style="background-image: radial-gradient(circle at center, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.45) 100%), url('https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2070'); background-size: cover; background-position: center; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem;"
    )

def global_header(state: AppState):
    return ui.div(
        ui.div(ui.div(style="width: 10px; height: 32px; background: #E50914; border-radius: 4px; margin-right: 12px;"), ui.div(ui.h3(state.main_menu(), style="font-size: 18px; color: #111111; font-weight: 800; margin: 0; line-height: 1.2;"), ui.span(f"Logged in as: {state.user_display_name()} ({state.role()})", style="font-size: 12px; color: #4A5568;"), style="display: flex; flex-direction: column; align-items: flex-start;"), style="display: flex; align-items: center;"),
        ui.div(
            ui.tags.button(ui.tags.i(class_="fa-solid fa-bullhorn", style="margin-right: 6px; color: #1A202C; font-size: 14px;"), "Panduan & Logic", onclick="Shiny.setInputValue('btn_open_panduan_modal', Math.random(), {priority: 'event'})", style="background: #E2E8F0; color: #1A202C; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;"
            ),
            ui.div(
                ui.div(
                    # --- TITIK HIJAU BERKEDIP ---
                    ui.div(
                        style="width: 8px; height: 8px; background: #10B981; border-radius: 50%; margin-right: 6px; animation: blinkAnimation 1.5s infinite ease-in-out;",
                        class_="blink-online"
                    ),
                    ui.span("ONLINE", style="font-size: 12px; font-weight: 800; color: #065F46;"),
                    style="display: flex; align-items: center;"
                ),
                ui.div(
                    ui.span(str(state.login_timestamp_ms()), id="login-time-store", style="display: none;"),
                    ui.tags.i(class_="fa-regular fa-clock", style="font-size: 12px; color: #4A5568; margin-right: 4px;"),
                    ui.span("00:00:00", id="live-timer", style="color: #4A5568; font-weight: bold; font-size: 12px; font-family: monospace;"),
                    style="display: flex; align-items: center; justify-content: center;"
                ),
                style="display: flex; flex-direction: column; align-items: center; gap: 2px;"
            ),
            style="display: flex; align-items: center; gap: 1.25rem;"
        ),
        style="padding: 12px 20px; background: #D1FAE5; border: 1.5px solid #A7F3D0; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 1rem;"
    )