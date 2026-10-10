import os
import json
import random
import base64
from datetime import datetime
import pandas as pd 
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
        // --- 1. DEFINISI ROUTING MENU DI PALING AWAL (ANTI-UNDEFINED) ---
        function getContainer() {
            return document.getElementById("main-scroll-container");
        }

        window.setMenuRoute = function(menuName, slug) {
            try {
                if (typeof userScrollTop !== 'undefined') userScrollTop = 0;
                let c = getContainer();
                if (c) c.scrollTop = 0;

                let basePath = window.location.pathname.replace(/index\.html$/, '');
                if (!basePath.endsWith('/')) basePath += '/';
                if (window.history.pushState) window.history.pushState(null, '', basePath + '#' + slug);
                else window.location.hash = '#' + slug;
            } catch(e) {
                try { window.location.hash = '#' + slug; } catch(err) {}
            }
            if (window.Shiny && window.Shiny.setInputValue) {
                Shiny.setInputValue('select_menu_item', menuName, {priority: 'event'});
            }
        };

        window.updateUrlMenu = function(menuName) {
            try {
                let slug = menuName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
                if (window.history.pushState) window.history.pushState(null, '', '#' + slug);
                else window.location.hash = '#' + slug;
            } catch(e) {}
        };

        // --- 2. GEMBOK OTOMATIS JUDUL & FAVICON ---
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

        // --- 3. ENGINE PAGINASI CEPAT (0ms) ---
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

        // --- 4. HUMAN-AWARE ZERO-GLITCH SCROLL ENGINE ---
        let userScrollTop = 0;
        let isHumanScrolling = false;
        let humanScrollTimer = null;
        let isFileInteracting = false;

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

        document.addEventListener('scroll', function(e) {
            let c = getContainer();
            if (!c) return;

            if (e.target === c || e.target === document) {
                if (isHumanScrolling) {
                    userScrollTop = c.scrollTop;
                } else if (userScrollTop > 0 && c.scrollTop === 0) {
                    c.scrollTop = userScrollTop;
                }
            }
        }, true);

        // --- 5. SPINNER CONTROLLER ---
        window.hideGlobalSpinner = function() {
            clearTimeout(window.spinnerSafetyTimer);
            if (document.body) document.body.classList.remove('process-running');
            let spinner = document.getElementById('global_reflex_loading');
            if (spinner) spinner.style.display = 'none';
        };

        window.showGlobalSpinner = function() {
            let spinner = document.getElementById('global_reflex_loading');
            if (spinner) spinner.style.display = 'flex';
            if (document.body) document.body.classList.add('process-running');

            clearTimeout(window.spinnerSafetyTimer);
            window.spinnerSafetyTimer = setTimeout(function() {
                window.hideGlobalSpinner();
            }, 120000);
        };

        // AMAN: Tunggu DOMContentLoaded agar document.body tidak NULL saat di-observe
        document.addEventListener("DOMContentLoaded", function() {
            if (document.body) {
                let modalObserver = new MutationObserver(function() {
                    let hasModal = document.getElementById('success-modal-overlay') || 
                                   document.getElementById('error-modal-overlay') ||
                                   document.querySelector('.shiny-notification');
                    if (hasModal) {
                        window.hideGlobalSpinner();
                    }
                });
                modalObserver.observe(document.body, { childList: true, subtree: true });
            }

            let h = window.location.hash.replace('#', '').trim();
            if (h && window.Shiny) {
                setTimeout(function() { Shiny.setInputValue('initial_url_hash', h, {priority: 'event'}); }, 500);
            }
        });
        // --- 6. SHINY EVENT LISTENERS (HAPUS SHINY:IDLE AGAR TIDAK MATI PREMATUR) ---
        if (window.jQuery) {
            $(document).on('shiny:fileuploaded shiny:inputchanged', function() {
                let c = getContainer();
                if (c && userScrollTop > 0) {
                    c.scrollTop = userScrollTop;
                }
            });
            // shiny:idle sengaja tidak mematikan spinner agar spinner tetap berputar sampai komputasi Python selesai
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

        #global_reflex_loading { display: none; cursor: pointer; }
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
def ongkir_dark_card(title: str, val_str: str, border_color: str, text_color: str):
    return ui.div(
        ui.span(title, style="color: #A0AEC0; font-size: 0.85rem; font-weight: bold; display: block; margin-bottom: 4px;"),
        ui.span(val_str, style=f"color: {text_color}; font-size: 1.7rem; font-weight: 800;"),
        style=f"""
            background: linear-gradient(135deg, #1a1d2e 0%, #252a3d 100%);
            padding: 16px 18px;
            border-radius: 12px;
            border-left: 5px solid {border_color};
            box-shadow: 2px 4px 15px rgba(0,0,0,0.3);
            width: 100%;
        """
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
    filtered_data = state.get_filtered_ongkir()
    filtered_ids = [str(r.get("id")) for r in filtered_data if r.get("id") is not None]
    
    is_all_selected = len(filtered_ids) > 0 and all(item_id in set(state.selected_ids()) for item_id in filtered_ids)
    selected_count = len(state.selected_ids())

    del_btn_ui = ui.tags.button(
        f"🗑️ HAPUS ({selected_count}) DATA", 
        onclick="Shiny.setInputValue('btn_open_delete_modal', Math.random(), {priority: 'event'})", 
        style="background: #E53E3E; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px;"
    ) if selected_count > 0 else ui.div()

    btn_select_all_text = "☑️ Batal Pilih Semua" if is_all_selected else "☑️ Pilih Semua"
    select_all_btn = ui.tags.button(
        btn_select_all_text,
        onclick="Shiny.setInputValue('btn_toggle_select_all', Math.random(), {priority: 'event'});",
        style="background: #EDF2F7; color: #2D3748; border: 1.5px solid #CBD5E0; border-radius: 6px; font-weight: 700; font-size: 12px; padding: 6px 12px; cursor: pointer;"
    ) if len(filtered_ids) > 0 else ui.div()

    select_options = [ui.tags.option(opt, value=opt, selected=(opt == state.filter_ekspedisi())) for opt in state.get_list_ekspedisi_options()]

    table_rows = [
        ui.tags.tr(
            ui.tags.td(
                ui.tags.input(
                    type="checkbox", 
                    checked=(str(r.get("id", "")) in set(state.selected_ids())), 
                    onchange=f"Shiny.setInputValue('toggle_row_id', '{r.get('id', '')}', {{priority: 'event'}})",
                    style="cursor: pointer; transform: scale(1.15);"
                ),
                style="text-align: center;"
            ),
            ui.tags.td(str(r.get("created_at", r.get("tanggal", "")))), 
            ui.tags.td(str(r.get("supplier", ""))), 
            ui.tags.td(str(r.get("ekspedisi", ""))),
            ui.tags.td(str(safe_int(r.get("total_koli", r.get("koli", 0))))), 
            ui.tags.td(f"Rp {safe_int(r.get('total_ongkir', 0)):,}")
        ) for r in filtered_data
    ]

    has_date_filter = bool(state.filter_tgl_start() or state.filter_tgl_end())
    reset_tgl_btn = ui.tags.button(
        "🔄 Reset Tgl",
        onclick="Shiny.setInputValue('btn_reset_filter_tgl', Math.random(), {priority: 'event'});",
        style="background: #EDF2F7; color: #4A5568; border: 1.5px solid #CBD5E0; border-radius: 8px; font-weight: 700; font-size: 12px; padding: 5px 10px; cursor: pointer; margin-left: 6px;"
    ) if has_date_filter else ui.div()

    return ui.div(
        # --- KONTROL FILTER & BUTTONS ---
        ui.div(
            ui.div(
                ui.div(
                    ui.span("EKSPEDISI:", style="font-size: 12px; font-weight: 800; color: #111111; margin-right: 6px;"),
                    ui.tags.select(
                        *select_options, 
                        id="select_filter_ekspedisi", 
                        onchange="Shiny.setInputValue('change_filter_ekspedisi', this.value, {priority: 'event'})", 
                        style="background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #1A202C !important; border-radius: 8px !important; font-weight: 800 !important; width: 150px; padding: 5px 8px; cursor: pointer; font-size: 12px;"
                    ),
                    style="display: flex; align-items: center;"
                ),
                ui.div(
                    ui.span("TGL AWAL:", style="font-size: 12px; font-weight: 800; color: #111111; margin-left: 10px; margin-right: 6px;"),
                    ui.tags.input(
                        type="date",
                        id="filter_tgl_start",
                        value=state.filter_tgl_start(),
                        onchange="Shiny.setInputValue('change_filter_tgl_start', this.value, {priority: 'event'})",
                        style="background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #1A202C !important; border-radius: 8px !important; font-weight: 700 !important; padding: 4px 8px; font-size: 12px; cursor: pointer;"
                    ),
                    style="display: flex; align-items: center;"
                ),
                ui.div(
                    ui.span("TGL AKHIR:", style="font-size: 12px; font-weight: 800; color: #111111; margin-left: 8px; margin-right: 6px;"),
                    ui.tags.input(
                        type="date",
                        id="filter_tgl_end",
                        value=state.filter_tgl_end(),
                        onchange="Shiny.setInputValue('change_filter_tgl_end', this.value, {priority: 'event'})",
                        style="background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #1A202C !important; border-radius: 8px !important; font-weight: 700 !important; padding: 4px 8px; font-size: 12px; cursor: pointer;"
                    ),
                    style="display: flex; align-items: center;"
                ),
                reset_tgl_btn,
                style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px;"
            ), 
            ui.div(
                select_all_btn,
                del_btn_ui,
                style="display: flex; align-items: center; gap: 8px;"
            ),
            style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-top: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap; gap: 10px;"
        ),

        # --- 3 ROW METRIC BOXES LENGKAP (PERSIS DENGAN KODE STREAMLIT) ---
        ui.div(
            # ROW 1: TOTAL KESELURUHAN (ALL)
            ui.div(
                ongkir_dark_card("💰 TOTAL BIAYA ALL", state.metric_total_biaya_all(), "#38BDF8", "#38BDF8"),
                ongkir_dark_card("📦 TOTAL KOLI ALL", state.metric_total_koli_all(), "#38BDF8", "#FFFFFF"),
                ongkir_dark_card("📊 AVG COST ALL", state.metric_avg_cost_all(), "#38BDF8", "#38BDF8"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),

            # ROW 2: BARANG DATANG (HIJAU NEON #00EB93)
            ui.div(
                ongkir_dark_card("🚚 BIAYA BARANG DATANG", state.metric_biaya_datang(), "#00EB93", "#00EB93"),
                ongkir_dark_card("📦 KOLI BARANG DATANG", state.metric_koli_datang(), "#00EB93", "#00EB93"),
                ongkir_dark_card("📊 AVG COST BARANG DATANG", state.metric_avg_datang(), "#00EB93", "#00EB93"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1rem;"
            ),

            # ROW 3: RTO (MERAH NEON #FF4B4B)
            ui.div(
                ongkir_dark_card("🔄 BIAYA RTO", state.metric_biaya_rto(), "#FF4B4B", "#FF4B4B"),
                ongkir_dark_card("📦 KOLI RTO", state.metric_koli_rto(), "#FF4B4B", "#FF4B4B"),
                ongkir_dark_card("📊 AVG COST RTO", state.metric_avg_rto(), "#FF4B4B", "#FF4B4B"),
                style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; width: 100%; margin-bottom: 1.5rem;"
            ),
            style="width: 100%;"
        ),

        # --- TABEL DATA ---
        ui.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th(
                            ui.tags.input(
                                type="checkbox", 
                                checked=is_all_selected,
                                onchange="Shiny.setInputValue('btn_toggle_select_all', Math.random(), {priority: 'event'});",
                                title="Pilih Semua / Batal Semua",
                                style="cursor: pointer; transform: scale(1.2);"
                            ),
                            style="text-align: center; width: 45px;"
                        ), 
                        ui.tags.th("TANGGAL"), 
                        ui.tags.th("SUPPLIER"), 
                        ui.tags.th("EKSPEDISI"), 
                        ui.tags.th("KOLI"), 
                        ui.tags.th("TOTAL ONGKIR")
                    ), 
                    style="background-color: #CBD5E0 !important;"
                ), 
                ui.tags.tbody(*table_rows) if len(table_rows) > 0 else ui.tags.tr(
                    ui.tags.td("Tidak ada transaksi ongkir.", colspan="6", style="text-align: center; color: #718096; padding: 2rem;")
                ), 
                class_="custom-clean-table"
            ), 
            style="background: #FFFFFF; border-radius: 16px; border: 2.5px solid #1A202C; padding: 1rem; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.04); overflow-x: auto;"
        ),
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
            ui.div(ui.input_selectize("so_bin_cov", "📡 BIN Coverage :", choices=list_bin_cov, multiple=True, width="100%"), style="flex: 1; min-width: 200px;"),
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
# VIEW JUSTIFICATION SO (DENGAN DROPDOWN MODE REVERSAL & NON REVERSAL)
# ==============================================================================
def justification_so_view(state: AppState):
    mode_selector = ui.div(
        ui.div(
            ui.span("🎯 PILIH METODE JUSTIFIKASI SO:", style="font-weight: 800; color: #1A202C; font-size: 13px; margin-bottom: 6px; display: block; letter-spacing: 0.5px;"),
            ui.tags.select(
                ui.tags.option("-- Pilih Mode Justifikasi SO --", value="", selected=(state.jso_mode() == "")),
                ui.tags.option("1. JUSTIFIKASI REVERSAL (CROSS-CHECK PBI HISTORY)", value="JUSTIFIKASI REVERSAL", selected=(state.jso_mode() == "JUSTIFIKASI REVERSAL")),
                ui.tags.option("2. JUSTIFIKASI NON REVERSAL (ANALISIS SYSTEM & STOCK)", value="JUSTIFIKASI NON REVERSAL", selected=(state.jso_mode() == "JUSTIFIKASI NON REVERSAL")),
                id="select_jso_mode_input",
                onchange="Shiny.setInputValue('change_jso_mode', this.value, {priority: 'event'})",
                style="width: 100%; padding: 10px 14px; background-color: #FFFFFF; color: #1A202C; font-weight: 800; font-size: 14px; border: 2px solid #CBD5E0; border-radius: 8px; outline: none; cursor: pointer;"
            ),
            style="width: 100%;"
        ),
        style="background: white; padding: 1.25rem 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);"
    )

    dynamic_body = ui.output_ui("jso_dynamic_body_ui")

    return ui.div(
        mode_selector,
        dynamic_body,
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
    list_sub_kat = [
        "BAG", "BALL", "BASELAYER", "BOTTLE", "CLEANNING & CARE", "EXTRA SHOES", 
        "HARDWARE", "JACKET", "JERSEY", "LOWER BODY", "NUTRITION", "OTHER", 
        "OTHERS", "PANTS", "RACKET", "SANDALS", "SET APPAREL", "SHIRT", 
        "SHOES", "SHORT", "SWLM", "UKNOWN SC", "UNDERLAYER", "UPPER BODY"
    ]

    filter_section = ui.div(
        ui.h4("🔍 Filter Sub Kategori (Opsional)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.input_selectize(
            "bs_filter_sub", "📁 Pilih Sub Kategori (Kolom G):", 
            choices=list_sub_kat, multiple=True, width="100%"
        ),
        style="background: white; padding: 1.25rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
    )

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
        filter_section,
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


# ==============================================================================
# VIEW: VALIDATION BARCODE SKU (2-STAGE VERIFICATION & PIVOT)
# ==============================================================================
def validation_barcode_sku_view(state: AppState):
    upload_section = ui.div(
        ui.h4("📥 Upload Dokumen Scan & List Perubahan SKU", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
        ui.div(
            custom_uploader_box("uploader_vbs_scan", "1. File Data Scan"),
            custom_uploader_box("uploader_vbs_list", "2. File List Perubahan SKU"),
            style="display: flex; gap: 1rem; width: 100%; margin-bottom: 0.5rem; flex-wrap: wrap;"
        ),
        ui.output_ui("vbs_action_btn_ui"),
        style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )

    results_section = ui.output_ui("vbs_results_container")

    return ui.div(
        upload_section,
        results_section,
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# VIEW: PERCENTAGE DISPLAY CONTROL & REFILL TOKO (DUAL TAB VIEW)
# ==============================================================================
def percentage_display_view(state: AppState):
    upload_section = ui.div(
        ui.div(
            ui.h4("📥 Upload Stock System (All Stock Multiple Adjustment)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("upload_percentage_display_file", "Pilih File Stock (Excel / CSV)"),
            ui.output_ui("percentage_display_action_btn_ui"),
            style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
        )
    )

    results_section = ui.output_ui("percentage_display_results_container")

    return ui.div(
        upload_section,
        results_section,
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# VIEW: LATIHAN FORMULA EXCEL (CLEAN & ON-DEMAND GENERATE)
# ==============================================================================
def excel_practice_view(state: AppState):
    return ui.div(
        # Header Banner
        ui.div(
            ui.div(
                ui.div(
                    ui.tags.i(class_="fa-solid fa-graduation-cap", style="color: #FFFFFF; font-size: 24px;"),
                    style="width: 44px; height: 44px; background: linear-gradient(135deg, #10B981 0%, #059669 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 12px;"
                ),
                ui.div(
                    ui.h3("E-Learning Excel Formula Logistic Retail (Auto-Grading)", style="font-size: 18px; font-weight: 800; color: #1A202C; margin: 0;"),
                    ui.p("Soal dibuat dinamis dengan berbagai variasi model tabel kerja (SUM, COUNT/COUNTA, SUMIF, COUNTIF, SUMIFS, COUNTIFS, IF, XLOOKUP).", style="font-size: 13px; color: #718096; margin: 0;")
                ),
                style="display: flex; align-items: center;"
            ),
            style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),

        # TAHAP 1: DOWNLOAD SOAL (BERSIH - GENERATE ON-DEMAND SAAT KLIK)
        ui.div(
            ui.div(
                ui.div(
                    ui.h4("1️⃣ TAHAP 1: Download Lembar Kerja Excel", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 4px 0;"),
                    ui.p("Klik tombol di sebelah kanan untuk men-generate paket soal acak. Lengkapi seluruh sel/kolom berlatar belakang KUNING dengan formula Excel.", style="color: #718096; font-size: 13px; margin: 0;"),
                ),
                ui.download_button(
                    "btn_dl_excel_practice",
                    ui.tags.span(
                        ui.tags.i(class_="fa-solid fa-cloud-arrow-down", style="margin-right: 8px; font-size: 14px;"),
                        "GENERATE & DOWNLOAD PAKET SOAL (.XLSX)"
                    ),
                    onclick="window.hideGlobalSpinner(); document.body.classList.remove('process-running'); setTimeout(function() { window.hideGlobalSpinner(); }, 400);",
                    style="background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%); color: white; font-weight: 800; border-radius: 8px; border: none; padding: 10px 22px; cursor: pointer; font-size: 13px; box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3); white-space: nowrap;"
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-wrap: wrap; gap: 12px;"
            ),
            style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),

        # TAHAP 2: UPLOAD JAWABAN & KOREKSI OTOMATIS
        ui.div(
            ui.h4("2️⃣ TAHAP 2: Upload File Excel yang Telah Diisi & Koreksi Otomatis", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
            custom_uploader_box("upload_exam_answer_file", "Upload File Excel Peserta yang Sudah Lengkap"),
            ui.output_ui("excel_practice_action_btn_ui"),
            style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.25rem;"
        ),

        # TAMPILAN SCORECARD & EVALUASI
        ui.output_ui("excel_practice_results_container"),
        style="width: 100%; padding: 1rem;"
    )


# ==============================================================================
# VIEW: FORM AUDITOR (5 TAB EXTENDED AUDIT PACK DENGAN DATABASE & TTD)
# ==============================================================================
def auditor_view(state: AppState):
    # KARTU ATAS: UPLOADER & FILTER DROPDOWN AUDITOR
    top_control = ui.div(
        ui.div(
            ui.h4("📥 1. Upload All Data Stock (Multiple Adjustment)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
            custom_uploader_box("upload_auditor_file", "Upload File Stock (Otomatis Mengecualikan BIN Karantina)"),
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-play", style="margin-right: 6px; font-size: 14px;"), "BACA FILE STOCK"),
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_load_auditor_file', Math.random(), {priority: 'event'});",
                    class_="btn-red-gradient"
                ),
                style="display: flex; justify-content: flex-end; width: 100%; margin-top: 0.5rem;"
            ),
            style="flex: 1; min-width: 320px;"
        ),
        ui.div(
            ui.h4("🎯 2. Filter Dropdown Target Audit", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
            ui.div(ui.input_selectize("aud_filter_brand", "🏷️ Brand (Kolom D):", choices=state.auditor_list_brand(), multiple=True, width="100%"), style="margin-bottom: 0.5rem;"),
            ui.div(ui.input_selectize("aud_filter_sub", "🗂️ Sub Kategori (Kolom G):", choices=state.auditor_list_sub(), multiple=True, width="100%"), style="margin-bottom: 0.5rem;"),
            ui.div(ui.input_selectize("aud_filter_bin", "🏭 BIN / Rak (Kolom B):", choices=state.auditor_list_bin(), multiple=True, width="100%")),
            style="flex: 1; min-width: 320px;"
        ),
        style="display: flex; gap: 1.5rem; flex-wrap: wrap; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem;"
    )

    # --------------------------------------------------------------------------
    # TAB 1: ENGAGEMENT DETAILS (DENGAN INPUT COUNTER SINKRON KE TAB 2)
    # --------------------------------------------------------------------------
    tab1_eng = ui.div(
        ui.h4("📋 Engagement Details (ISA 501 / PSAK 14)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
        ui.div(
            ui.div(ui.span("🏢 Company Name:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_company", type="text", value="PT ZONA KARYA NUSANTARA", class_="form-control"), style="flex: 1; min-width: 220px;"),
            ui.div(ui.span("🏬 Warehouse Branch:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_branch", type="text", value="SZ SURABAYA", class_="form-control"), style="flex: 1; min-width: 180px;"),
            ui.div(ui.span("📅 Stock Count Date:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_date", type="text", value=datetime.now().strftime("%d %B %Y").upper(), class_="form-control"), style="flex: 1; min-width: 160px;"),
            style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;"
        ),
        ui.div(
            ui.div(ui.span("⏰ Count Start Time:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_start_time", type="text", value="08:00", class_="form-control"), style="flex: 1; min-width: 160px;"),
            ui.div(ui.span("⏰ Count End Time:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_end_time", type="text", value="17:00", class_="form-control"), style="flex: 1; min-width: 160px;"),
            ui.div(
                ui.span("📋 Count Method:", style="font-size: 12px; font-weight: 800;"),
                ui.tags.select(
                    ui.tags.option("Full count (wall-to-wall)", value="Full count (wall-to-wall)"),
                    ui.tags.option("Cycle count", value="Cycle count"),
                    ui.tags.option("Sample count", value="Sample count"),
                    id="aud_method", class_="form-control"
                ), style="flex: 1; min-width: 200px;"
            ),
            style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;"
        ),
        ui.div(
            ui.div(ui.span("👤 Lead Auditor:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_lead", type="text", placeholder="Nama Lead Auditor...", class_="form-control"), style="flex: 1; min-width: 200px;"),
            ui.div(ui.span("👤 Warehouse/Ops. Manager:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_manager", type="text", placeholder="Nama Manager Ops...", class_="form-control"), style="flex: 1; min-width: 200px;"),
            ui.div(ui.span("👤 Count Team Supervisor:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_supervisor", type="text", placeholder="Nama Supervisor...", class_="form-control"), style="flex: 1; min-width: 200px;"),
            # 👇 POIN 1: INPUT NAMA COUNTER DISINKRONKAN LANGSUNG KE TAB 2 👇
            ui.div(
                ui.span("📦 Counter Name / Tim Hitung (Sync ke Tab 2):", style="font-size: 12px; font-weight: 800; color: #E50914;"),
                ui.tags.input(
                    id="aud_counter", type="text", value="Counter A", placeholder="Contoh: Counter A / Budi...",
                    oninput="Shiny.setInputValue('change_auditor_counter_name', this.value, {priority: 'event'})",
                    class_="form-control", style="border: 1.5px solid #E50914;"
                ),
                style="flex: 1; min-width: 200px;"
            ),
            ui.div(ui.span("💵 Currency:", style="font-size: 12px; font-weight: 800;"), ui.tags.input(id="aud_currency", type="text", value="IDR", class_="form-control"), style="width: 100px;"),
            style="display: flex; gap: 1rem; flex-wrap: wrap;"
        ),
        style="padding: 1rem 0;"
    )

    # --------------------------------------------------------------------------
    # TAB 2: STOCK COUNT SHEET (BISA DIISI DI WEB & UPLOAD EXCEL YANG SUDAH DIISI)
    # --------------------------------------------------------------------------
    tab2_count = ui.div(
        # Kotak Upload Excel yang Sudah Diisi
        ui.div(
            ui.div(
                ui.h4("📥 Upload Hasil Count Sheet yang Telah Diisi (.xlsx)", style="font-size: 14px; font-weight: 800; color: #1A202C; margin: 0 0 4px 0;"),
                ui.p("Unduh format count sheet di bawah, isi kolom 'Physical Count', lalu upload kembali file tersebut ke sini untuk sinkronisasi otomatis.", style="color: #718096; font-size: 12px; margin: 0;"),
            ),
            ui.div(
                ui.input_file("upload_filled_count_sheet", None, accept=[".xlsx", ".xls"], button_label="Pilih File Terisi", placeholder="Upload file hasil hitung..."),
                ui.tags.button(
                    ui.tags.i(class_="fa-solid fa-cloud-arrow-up", style="margin-right: 6px;"), "SINKRONISASI HASIL",
                    onclick="window.showGlobalSpinner(); Shiny.setInputValue('btn_execute_import_count_sheet', Math.random(), {priority: 'event'})",
                    style="background: #10B981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 800; font-size: 12px; cursor: pointer; white-space: nowrap;"
                ),
                style="display: flex; gap: 8px; align-items: center;"
            ),
            style="background: #F0FDF4; border: 1.5px dashed #86EFAC; padding: 1.25rem; border-radius: 10px; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;"
        ),
        # Kontainer Hasil Tabel & Form Isi Web Langsung
        ui.output_ui("auditor_results_container"),
        style="padding: 0.5rem 0;"
    )

    # --------------------------------------------------------------------------
    # TAB 3: OBSERVATIONS & FINDINGS (DENGAN TOMBOL TAMBAH DINAMIS)
    # --------------------------------------------------------------------------
    tab3_obs = ui.div(
        ui.h4("🔍 Auditor Observations & Findings", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.p("Catat seluruh temuan dan observasi fisik auditor. Gunakan tombol 'Tambah Temuan' untuk memasukkan banyak data.", style="color: #718096; font-size: 13px; margin-bottom: 1rem;"),
        # Form Input Temuan
        ui.div(
            ui.div(
                ui.div(ui.span("Area / Lokasi:", style="font-weight: 700; font-size: 12px;"), ui.tags.input(id="obs_area_in", type="text", value="Condition of stock", class_="form-control"), style="flex: 1; min-width: 160px;"),
                ui.div(ui.span("Kasus / Temuan Fisik:", style="font-weight: 700; font-size: 12px;"), ui.tags.input(id="obs_case_in", type="text", placeholder="Contoh: Kardus basah, barang tercecer...", class_="form-control"), style="flex: 2; min-width: 250px;"),
                ui.div(
                    ui.span("Tingkat Risiko:", style="font-weight: 700; font-size: 12px;"),
                    ui.tags.select(ui.tags.option("Medium", value="Medium"), ui.tags.option("High", value="High"), ui.tags.option("Low", value="Low"), id="obs_risk_in", class_="form-control"),
                    style="width: 130px;"
                ),
                style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.75rem;"
            ),
            ui.div(
                ui.div(ui.span("Rekomendasi Auditor:", style="font-weight: 700; font-size: 12px;"), ui.tags.input(id="obs_recom_in", type="text", placeholder="Rekomendasi penanganan...", class_="form-control"), style="flex: 2; min-width: 250px;"),
                ui.div(ui.span("Status:", style="font-weight: 700; font-size: 12px;"), ui.tags.select(ui.tags.option("Open", value="Open"), ui.tags.option("Closed", value="Closed"), id="obs_status_in", class_="form-control"), style="width: 130px;"),
                ui.div(
                    ui.tags.button(
                        ui.tags.i(class_="fa-solid fa-plus", style="margin-right: 6px;"), "Tambah Temuan",
                        onclick="""
                            let a = document.getElementById('obs_area_in').value;
                            let c = document.getElementById('obs_case_in').value;
                            let r = document.getElementById('obs_risk_in').value;
                            let rec = document.getElementById('obs_recom_in').value;
                            let s = document.getElementById('obs_status_in').value;
                            if(!c.trim()) { alert('Kasus/Temuan tidak boleh kosong!'); return; }
                            Shiny.setInputValue('btn_add_obs_finding', {area: a, case: c, risk: r, recom: rec, status: s}, {priority: 'event'});
                            document.getElementById('obs_case_in').value = '';
                            document.getElementById('obs_recom_in').value = '';
                        """,
                        style="background: #E50914; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer; height: 38px; display: flex; align-items: center; margin-top: 18px;"
                    )
                ),
                style="display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-start;"
            ),
            style="background: #F8FAFC; border: 1.5px solid #E2E8F0; padding: 1.25rem; border-radius: 10px; margin-bottom: 1.5rem;"
        ),
        # Tabel List Temuan Dinamis
        ui.output_ui("auditor_findings_table_ui"),
        style="padding: 0.5rem 0;"
    )

    # --------------------------------------------------------------------------
    # TAB 4: SIGN-OFF (DENGAN NAMA & CANVAS DIGITAL TANDA TANGAN)
    # --------------------------------------------------------------------------
    tab4_sign = ui.div(
        ui.h4("✍️ Stock Count Sign-Off (Nama & Tanda Tangan Digital)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.5rem;"),
        ui.p("Isi nama penandatangan dan bubuhkan tanda tangan langsung pada kotak kanvas di bawah.", style="color: #718096; font-size: 13px; margin-bottom: 1.25rem;"),
        
        # 4 Card Penandatangan
        ui.div(
            # 1. Counter
            ui.div(
                ui.strong("1. Counter (Penghitung)", style="font-size: 13px; color: #1A202C; display: block; margin-bottom: 4px;"),
                ui.tags.input(id="sign_counter_name_in", type="text", placeholder="Nama Counter...", class_="form-control", style="margin-bottom: 8px; font-size: 12px;"),
                ui.tags.canvas(id="canvas_sign_counter", width="240", height="90", style="border: 1px dashed #CBD5E0; border-radius: 6px; background: #FFF; cursor: crosshair; display: block; width: 100%;"),
                ui.tags.button("Bersihkan TTD", type="button", onclick="window.clearSignCanvas('canvas_sign_counter')", style="background: #EDF2F7; border: 1px solid #CBD5E0; font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-top: 4px; cursor: pointer;"),
                style="flex: 1; min-width: 220px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;"
            ),
            # 2. Supervisor
            ui.div(
                ui.strong("2. Count Supervisor", style="font-size: 13px; color: #1A202C; display: block; margin-bottom: 4px;"),
                ui.tags.input(id="sign_supervisor_name_in", type="text", placeholder="Nama Supervisor...", class_="form-control", style="margin-bottom: 8px; font-size: 12px;"),
                ui.tags.canvas(id="canvas_sign_spv", width="240", height="90", style="border: 1px dashed #CBD5E0; border-radius: 6px; background: #FFF; cursor: crosshair; display: block; width: 100%;"),
                ui.tags.button("Bersihkan TTD", type="button", onclick="window.clearSignCanvas('canvas_sign_spv')", style="background: #EDF2F7; border: 1px solid #CBD5E0; font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-top: 4px; cursor: pointer;"),
                style="flex: 1; min-width: 220px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;"
            ),
            # 3. Manager
            ui.div(
                ui.strong("3. Warehouse/Ops Manager", style="font-size: 13px; color: #1A202C; display: block; margin-bottom: 4px;"),
                ui.tags.input(id="sign_manager_name_in", type="text", placeholder="Nama Manager Ops...", class_="form-control", style="margin-bottom: 8px; font-size: 12px;"),
                ui.tags.canvas(id="canvas_sign_mgr", width="240", height="90", style="border: 1px dashed #CBD5E0; border-radius: 6px; background: #FFF; cursor: crosshair; display: block; width: 100%;"),
                ui.tags.button("Bersihkan TTD", type="button", onclick="window.clearSignCanvas('canvas_sign_mgr')", style="background: #EDF2F7; border: 1px solid #CBD5E0; font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-top: 4px; cursor: pointer;"),
                style="flex: 1; min-width: 220px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;"
            ),
            # 4. Lead Auditor
            ui.div(
                ui.strong("4. External Lead Auditor", style="font-size: 13px; color: #1A202C; display: block; margin-bottom: 4px;"),
                ui.tags.input(id="sign_lead_name_in", type="text", placeholder="Nama Lead Auditor...", class_="form-control", style="margin-bottom: 8px; font-size: 12px;"),
                ui.tags.canvas(id="canvas_sign_lead", width="240", height="90", style="border: 1px dashed #CBD5E0; border-radius: 6px; background: #FFF; cursor: crosshair; display: block; width: 100%;"),
                ui.tags.button("Bersihkan TTD", type="button", onclick="window.clearSignCanvas('canvas_sign_lead')", style="background: #EDF2F7; border: 1px solid #CBD5E0; font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-top: 4px; cursor: pointer;"),
                style="flex: 1; min-width: 220px; background: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;"
            ),
            style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem;"
        ),
        # Tombol Final Simpan ke Database
        ui.div(
            ui.tags.button(
                ui.tags.span(ui.tags.i(class_="fa-solid fa-floppy-disk", style="margin-right: 8px; font-size: 15px;"), "SIMPAN AUDIT KE DATABASE SUPABASE & GENERATE REPORT"),
                onclick="""
                    let getCanvasData = function(id) {
                        let c = document.getElementById(id);
                        return c ? c.toDataURL() : '';
                    };
                    let meta = {
                        company: document.getElementById('aud_company') ? document.getElementById('aud_company').value : '',
                        branch: document.getElementById('aud_branch') ? document.getElementById('aud_branch').value : '',
                        date: document.getElementById('aud_date') ? document.getElementById('aud_date').value : '',
                        start_time: document.getElementById('aud_start_time') ? document.getElementById('aud_start_time').value : '',
                        end_time: document.getElementById('aud_end_time') ? document.getElementById('aud_end_time').value : '',
                        method: document.getElementById('aud_method') ? document.getElementById('aud_method').value : '',
                        lead: document.getElementById('aud_lead') ? document.getElementById('aud_lead').value : '',
                        manager: document.getElementById('aud_manager') ? document.getElementById('aud_manager').value : '',
                        supervisor: document.getElementById('aud_supervisor') ? document.getElementById('aud_supervisor').value : '',
                        counter: document.getElementById('aud_counter') ? document.getElementById('aud_counter').value : 'Counter A',
                        currency: document.getElementById('aud_currency') ? document.getElementById('aud_currency').value : 'IDR',
                        sign_counter_name: document.getElementById('sign_counter_name_in') ? document.getElementById('sign_counter_name_in').value : '',
                        sign_counter_img: getCanvasData('canvas_sign_counter'),
                        sign_supervisor_name: document.getElementById('sign_supervisor_name_in') ? document.getElementById('sign_supervisor_name_in').value : '',
                        sign_supervisor_img: getCanvasData('canvas_sign_spv'),
                        sign_manager_name: document.getElementById('sign_manager_name_in') ? document.getElementById('sign_manager_name_in').value : '',
                        sign_manager_img: getCanvasData('canvas_sign_mgr'),
                        sign_lead_name: document.getElementById('sign_lead_name_in') ? document.getElementById('sign_lead_name_in').value : '',
                        sign_lead_img: getCanvasData('canvas_sign_lead')
                    };
                    window.showGlobalSpinner();
                    Shiny.setInputValue('btn_execute_save_audit_supabase', meta, {priority: 'event'});
                """,
                class_="btn-red-gradient",
                style="padding: 12px 24px; font-size: 14px; font-weight: 800; border-radius: 8px;"
            ),
            style="display: flex; justify-content: flex-end; width: 100%;"
        ),
        # JS Inisialisasi Canvas Tanda Tangan
        ui.tags.script("""
            function initSignCanvases() {
                ['canvas_sign_counter', 'canvas_sign_spv', 'canvas_sign_mgr', 'canvas_sign_lead'].forEach(function(id) {
                    let canvas = document.getElementById(id);
                    if (!canvas || canvas.dataset.initialized) return;
                    canvas.dataset.initialized = "true";
                    let ctx = canvas.getContext('2d');
                    ctx.lineWidth = 2;
                    ctx.lineCap = 'round';
                    ctx.strokeStyle = '#000000';
                    let drawing = false;

                    function getPos(e) {
                        let rect = canvas.getBoundingClientRect();
                        let clientX = e.clientX || (e.touches && e.touches[0].clientX);
                        let clientY = e.clientY || (e.touches && e.touches[0].clientY);
                        return { x: clientX - rect.left, y: clientY - rect.top };
                    }
                    function start(e) { drawing = true; let p = getPos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); }
                    function draw(e) { if (!drawing) return; let p = getPos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); }
                    function stop() { drawing = false; }

                    canvas.addEventListener('mousedown', start);
                    canvas.addEventListener('mousemove', draw);
                    window.addEventListener('mouseup', stop);
                    canvas.addEventListener('touchstart', function(e) { e.preventDefault(); start(e); });
                    canvas.addEventListener('touchmove', function(e) { e.preventDefault(); draw(e); });
                    canvas.addEventListener('touchend', stop);
                });
            }
            window.clearSignCanvas = function(id) {
                let canvas = document.getElementById(id);
                if (canvas) {
                    let ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
            };
            setTimeout(initSignCanvases, 600);
        """),
        style="padding: 0.5rem 0;"
    )

    # --------------------------------------------------------------------------
    # TAB 5: AUDIT HISTORY & DOWNLOAD PDF RESMI (POIN 5)
    # --------------------------------------------------------------------------
    tab5_history = ui.div(
        ui.div(
            ui.div(
                ui.h4("📂 Riwayat & Arsip Audit Pack (Tersimpan di Supabase)", style="font-size: 15px; font-weight: 800; color: #1A202C; margin: 0 0 4px 0;"),
                ui.p("Auditor dapat meninjau hasil stock opname terdahulu dan mengunduh laporan PDF resmi.", style="color: #718096; font-size: 13px; margin: 0;"),
            ),
            ui.tags.button(
                ui.tags.i(class_="fa-solid fa-arrows-rotate", style="margin-right: 6px;"), "Refresh History",
                onclick="Shiny.setInputValue('btn_refresh_audit_history', Math.random(), {priority: 'event'})",
                style="background: #EDF2F7; color: #2D3748; border: 1.5px solid #CBD5E0; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer;"
            ),
            style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 8px;"
        ),
        ui.output_ui("auditor_history_cards_ui"),
        ui.output_ui("auditor_pdf_downloader_container_ui"),
        style="padding: 0.5rem 0;"
    )

    # CARD NAVSET UTAMA 5 TAB
    main_tabs = ui.div(
        ui.navset_card_tab(
            ui.nav_panel("📋 1. ENGAGEMENT DETAILS", tab1_eng),
            ui.nav_panel("📦 2. STOCK COUNT SHEET", tab2_count),
            ui.nav_panel("🔍 3. OBSERVATIONS & FINDINGS", tab3_obs),
            ui.nav_panel("✍️ 4. SIGN-OFF", tab4_sign),
            ui.nav_panel("📂 5. AUDIT HISTORY & PDF", tab5_history),
            id="auditor_navset_tab"
        ),
        style="width: 100%; background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
    )

    return ui.div(
        top_control,
        main_tabs,
        style="width: 100%; padding: 1rem;"
    )

# ==============================================================================
# TABEL EDIT LANGSUNG DI WEB (INLINE EDITABLE - TANPA POP-UP)
# ==============================================================================
def render_auditor_editable_table(df_data, counter_name="Counter A"):
    if df_data is None or df_data.empty:
        return ui.div(
            ui.p("Tidak ada data. Muat file stock terlebih dahulu.", style="color: #718096; padding: 1.5rem; font-style: italic; text-align: center;"),
            style="background: white; border-radius: 8px; border: 1px solid #E2E8F0; width: 100%;"
        )

    headers = [
        "No.", "Bin Location", "SKU", "Description", "Category", 
        "UoM", "Qty System", "Physical Count (Ketik Disini)", "Variance Value", 
        "Counter", "Auditor Verified", "Remarks"
    ]
    th_cells = [ui.tags.th(h, style="background: #1A365D; color: white; padding: 10px; font-size: 12px; white-space: nowrap; text-align: center;" if h in ["No.","UoM","Qty System","Physical Count (Ketik Disini)","Variance Value","Auditor Verified"] else "background: #1A365D; color: white; padding: 10px; font-size: 12px; white-space: nowrap;") for h in headers]

    tr_rows = []
    for idx, r in df_data.iterrows():
        sys_q = safe_int(r.get('Qty System', 0))
        phys_val = r.get('Physical Count', '')
        phys_str = str(phys_val) if phys_val != '' and not pd.isna(phys_val) else ''
        
        var_val = r.get('Variance Value', '')
        if var_val != '' and not pd.isna(var_val):
            v_int = safe_int(var_val)
            v_text = f"{v_int:+d}" if v_int != 0 else "0"
            v_color = "#10B981" if v_int == 0 else "#E53E3E"
        else:
            v_text = "-"
            v_color = "#718096"

        ver_val = str(r.get('Auditor Verified', 'No'))
        rem_val = str(r.get('Remarks', '')) if not pd.isna(r.get('Remarks', '')) else ''

        # Input angka fisik langsung di baris tabel (warna kuning Excel)
        input_phys = ui.tags.input(
            id=f"phys_in_{idx}",
            type="number",
            min="0",
            value=phys_str,
            placeholder="0",
            oninput=f"window.onAuditorRowChange({idx}, {sys_q})",
            style="width: 90px; text-align: right; font-weight: 800; font-size: 13px; padding: 5px 8px; border-radius: 6px; border: 1.5px solid #CBD5E0; background-color: #FEFCBF; outline: none;"
        )

        # Dropdown verified langsung di tabel
        select_ver = ui.tags.select(
            ui.tags.option("No", value="No", selected=(ver_val == "No")),
            ui.tags.option("Yes", value="Yes", selected=(ver_val == "Yes")),
            id=f"ver_in_{idx}",
            onchange=f"window.onAuditorRowChange({idx}, {sys_q})",
            style="padding: 4px 8px; border-radius: 6px; border: 1.5px solid #CBD5E0; font-weight: 700; font-size: 12px; background: white; cursor: pointer;"
        )

        # Input catatan remarks langsung di tabel
        input_rem = ui.tags.input(
            id=f"rem_in_{idx}",
            type="text",
            value=rem_val,
            placeholder="Catatan...",
            onchange=f"window.onAuditorRowChange({idx}, {sys_q})",
            style="width: 140px; font-size: 12px; padding: 4px 8px; border-radius: 6px; border: 1px solid #CBD5E0; background: white; outline: none;"
        )

        tr_rows.append(ui.tags.tr(
            ui.tags.td(str(idx + 1), style="text-align: center; font-weight: bold;"),
            ui.tags.td(str(r.get('Bin Location', ''))),
            ui.tags.td(str(r.get('SKU', '')), style="font-weight: 700; color: #2B6CB0;"),
            ui.tags.td(str(r.get('Description', ''))),
            ui.tags.td(str(r.get('Category', ''))),
            ui.tags.td(str(r.get('UoM (PAIR / PCS)', 'PCS')), style="text-align: center;"),
            ui.tags.td(str(sys_q), id=f"sys_cell_{idx}", style="text-align: right; font-weight: 700;"),
            ui.tags.td(input_phys, style="text-align: center; background: #FFFDF0;"),
            ui.tags.td(
                ui.tags.span(v_text, id=f"var_cell_{idx}", style=f"font-weight: 800; font-size: 13px; color: {v_color};"),
                style="text-align: right; background: #F8FAFC;"
            ),
            ui.tags.td(counter_name, style="text-align: center; color: #4A5568; font-weight: 600;"),
            ui.tags.td(select_ver, style="text-align: center;"),
            ui.tags.td(input_rem)
        ))

    return ui.div(
        ui.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(*th_cells)),
                ui.tags.tbody(*tr_rows),
                class_="custom-clean-table",
                style="width: 100%; border-collapse: collapse;"
            ),
            style="overflow-x: auto; width: 100%; background: white; border-radius: 8px; border: 1px solid #E2E8F0;"
        ),
        ui.tags.script("""
            window.auditorDebounceTimers = window.auditorDebounceTimers || {};
            window.onAuditorRowChange = function(idx, sysQty) {
                let physEl = document.getElementById('phys_in_' + idx);
                let verEl = document.getElementById('ver_in_' + idx);
                let remEl = document.getElementById('rem_in_' + idx);
                let varCell = document.getElementById('var_cell_' + idx);

                let physStr = physEl ? physEl.value.trim() : '';
                let verVal = verEl ? verEl.value : 'No';
                let remVal = remEl ? remEl.value : '';

                if (varCell) {
                    if (physStr === '') {
                        varCell.innerText = '-';
                        varCell.style.color = '#718096';
                    } else {
                        let diff = parseInt(physStr) - parseInt(sysQty);
                        varCell.innerText = (diff > 0 ? '+' : '') + diff;
                        varCell.style.color = (diff === 0) ? '#10B981' : '#E53E3E';
                    }
                }

                clearTimeout(window.auditorDebounceTimers[idx]);
                window.auditorDebounceTimers[idx] = setTimeout(function() {
                    if (window.Shiny && Shiny.setInputValue) {
                        Shiny.setInputValue('auditor_row_inline_update', {
                            idx: idx,
                            phys: physStr,
                            ver: verVal,
                            rem: remVal
                        }, {priority: 'event'});
                    }
                }, 400);
            };
        """),
        style="width: 100%; margin-top: 0.5rem;"
    )

# ==============================================================================
# VIEW: MEMO PENGAJUAN (2 TAB: FORM PENGAJUAN & HISTORY APPROVAL)
# ==============================================================================
def memo_pengajuan_view(state: AppState):
    divisi_choices = [
        "MARKOM", "RETAIL / STORE", "OPERASIONAL", "PURCHASING", 
        "FINANCE & ACCOUNTING", "HRD & GA", "LOGISTIK DC", "IT SUPPORT"
    ]
    jenis_choices = [
        "Peminjaman Barang Display / Event",
        "Pengeluaran Sample Promosi & Endorsement",
        "Pengadaan Alat & Perlengkapan Kerja",
        "Mutasi Barang Antar Divisi / Cabang",
        "Penggantian Barang Rusak / Defect",
        "Lainnya"
    ]

    # --- TAB 1: FORM INPUT MEMO & LIST BARANG ---
    tab1_form = ui.div(
        ui.div(
            # Bagian Atas: Form Header Memo
            ui.div(
                ui.h4("📝 Identitas & Detail Pengajuan Memo", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 1rem;"),
                ui.div(
                    ui.div(
                        ui.span("Tanggal Pengajuan:", style="font-size: 12px; font-weight: 800; color: #2D3748; display: block; margin-bottom: 4px;"),
                        ui.input_date("memo_in_tanggal", None, value=datetime.now().strftime("%Y-%m-%d")),
                        style="flex: 1; min-width: 180px;"
                    ),
                    ui.div(
                        ui.span("Divisi Pemohon:", style="font-size: 12px; font-weight: 800; color: #2D3748; display: block; margin-bottom: 4px;"),
                        ui.input_select("memo_in_divisi", None, choices=divisi_choices, selected="MARKOM"),
                        style="flex: 1; min-width: 200px;"
                    ),
                    ui.div(
                        ui.span("Jenis Pengajuan:", style="font-size: 12px; font-weight: 800; color: #2D3748; display: block; margin-bottom: 4px;"),
                        ui.input_select("memo_in_jenis", None, choices=jenis_choices, selected=jenis_choices[0]),
                        style="flex: 1.5; min-width: 260px;"
                    ),
                    style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;"
                ),
                ui.div(
                    ui.div(
                        ui.span("Tujuan / Keperluan:", style="font-size: 12px; font-weight: 800; color: #2D3748; display: block; margin-bottom: 4px;"),
                        ui.tags.input(id="memo_in_tujuan", type="text", placeholder="Contoh: Keperluan Photoshoot Campaign Ramadhan / Event Surabaya", class_="form-control", style="width: 100%; border: 1.5px solid #CBD5E0; border-radius: 6px; padding: 8px 12px; font-size: 13px;"),
                        style="flex: 2; min-width: 280px;"
                    ),
                    ui.div(
                        ui.span("Diajukan Oleh (Nama PIC):", style="font-size: 12px; font-weight: 800; color: #2D3748; display: block; margin-bottom: 4px;"),
                        ui.tags.input(id="memo_in_pemohon", type="text", placeholder="Nama Pemohon...", class_="form-control", style="width: 100%; border: 1.5px solid #CBD5E0; border-radius: 6px; padding: 8px 12px; font-size: 13px;"),
                        style="flex: 1; min-width: 180px;"
                    ),
                    style="display: flex; gap: 1rem; flex-wrap: wrap;"
                ),
                style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem;"
            ),

            # Bagian Tengah: Input List Barang (SKU, Item Name, COGS, QTY)
            ui.div(
                ui.h4("📦 List Item Barang yang Diajukan", style="font-size: 15px; font-weight: 800; color: #1A202C; margin-bottom: 0.75rem;"),
                ui.div(
                    ui.div(ui.span("SKU Barang:", style="font-size: 11px; font-weight: 700;"), ui.tags.input(id="item_in_sku", type="text", placeholder="Contoh: SPT-SPE-42-01", class_="form-control"), style="flex: 1; min-width: 160px;"),
                    ui.div(ui.span("Item Name / Deskripsi:", style="font-size: 11px; font-weight: 700;"), ui.tags.input(id="item_in_name", type="text", placeholder="Nama Barang...", class_="form-control"), style="flex: 1.5; min-width: 220px;"),
                    ui.div(ui.span("COGS (Harga Pokok):", style="font-size: 11px; font-weight: 700;"), ui.tags.input(id="item_in_cogs", type="number", value="0", placeholder="Rp...", class_="form-control"), style="flex: 1; min-width: 130px;"),
                    ui.div(ui.span("Qty:", style="font-size: 11px; font-weight: 700;"), ui.tags.input(id="item_in_qty", type="number", value="1", min="1", class_="form-control"), style="width: 90px;"),
                    
                    # 1. Tombol Tambah Item Manual (Cukup 1 saja)
                    ui.div(
                        ui.tags.button(
                            ui.tags.i(class_="fa-solid fa-plus", style="margin-right: 6px;"), "Tambah Item",
                            onclick="Shiny.setInputValue('btn_add_item_to_memo', {sku: document.getElementById('item_in_sku').value, name: document.getElementById('item_in_name').value, cogs: document.getElementById('item_in_cogs').value, qty: document.getElementById('item_in_qty').value}, {priority: 'event'});",
                            style="background: #10B981; color: white; font-weight: 700; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; height: 38px; display: flex; align-items: center; margin-top: 18px;"
                        )
                    ),
                    # 2. Tombol Pop-up Bulk Upload Excel/CSV
                    ui.div(
                        ui.tags.button(
                            ui.tags.i(class_="fa-solid fa-file-excel", style="margin-right: 6px;"), "Bulk Upload Item",
                            onclick="Shiny.setInputValue('btn_open_memo_bulk_modal', Math.random(), {priority: 'event'});",
                            style="background: #3182CE; color: white; font-weight: 700; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; height: 38px; display: flex; align-items: center; margin-top: 18px;"
                        )
                    ),
                    style="display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: flex-start; margin-bottom: 1rem; background: #FFFFFF; border: 1px dashed #CBD5E0; padding: 1rem; border-radius: 8px;"
                ),
                ui.output_ui("memo_draft_items_table_ui"),
                style="margin-bottom: 1.5rem;"
            ),
            # Bagian Bawah: Tombol Submit Memo
            ui.div(
                ui.tags.button(
                    ui.tags.span(ui.tags.i(class_="fa-solid fa-paper-plane", style="margin-right: 8px; font-size: 15px;"), "SUBMIT MEMO PENGAJUAN & KIRIM NOTIFIKASI WA"),
                    onclick="""
                        let tujuan = document.getElementById('memo_in_tujuan') ? document.getElementById('memo_in_tujuan').value : '';
                        let pemohon = document.getElementById('memo_in_pemohon') ? document.getElementById('memo_in_pemohon').value : '';
                        Shiny.setInputValue('btn_execute_submit_memo', {tujuan: tujuan, pemohon: pemohon}, {priority: 'event'});
                    """,
                    class_="btn-red-gradient",
                    style="padding: 12px 24px; font-size: 14px; font-weight: 800;"
                ),
                style="display: flex; justify-content: flex-end; width: 100%;"
            ),
            style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0;"
        ),
        style="padding: 0.5rem 0;"
    )

    # --- TAB 2: RIWAYAT & WORKFLOW APPROVAL ---
    tab2_history = ui.div(
        ui.output_ui("memo_history_table_ui"),
        style="padding: 0.5rem 0;"
    )

    

    return ui.div(
        ui.navset_card_tab(
            ui.nav_panel("📝 BUAT MEMO PENGAJUAN", tab1_form, value="tab_memo_form"),
            ui.nav_panel("📊 HISTORY & APPROVAL TRACKING", tab2_history, value="tab_memo_history"),
            id="memo_navset"
        ),
        style="width: 100%; padding: 1rem;"
    )


def menu_item(label: str, target_menu: str, current_menu: str):
    import re
    is_active = (current_menu == target_menu)
    bg_style = (
        "background: linear-gradient(135deg, #E50914 0%, #B20710 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4);"
        if is_active else 
        "background: transparent; color: #CBD5E0; font-weight: 500;"
    )
    
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', target_menu).strip('-').lower()
    
    # Panggil fungsi navigasi dengan fallback langsung ke Shiny jika fungsi JS belum ter-load
    onclick_js = f"""
        if (typeof window.setMenuRoute === 'function') {{
            window.setMenuRoute('{target_menu}', '{slug}');
        }} else if (window.Shiny) {{
            Shiny.setInputValue('select_menu_item', '{target_menu}', {{priority: 'event'}});
        }}
    """
    
    return ui.tags.button(
        label, 
        type="button",
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