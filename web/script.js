// --- ИСТОРИЯ ДЛЯ CTRL+Z ---
let textHistory =[];
let historyStep = -1;

function saveHistoryState() {
    let ta = document.getElementById('p_text');
    if (!ta) return;
    
    let state = { val: ta.value, start: ta.selectionStart, end: ta.selectionEnd };
    
    // Не дублируем одинаковые состояния
    if (historyStep >= 0 && textHistory[historyStep].val === state.val) return;

    if (historyStep < textHistory.length - 1) {
        textHistory = textHistory.slice(0, historyStep + 1);
    }
    
    textHistory.push(state);
    if (textHistory.length > 50) textHistory.shift(); // Храним максимум 50 шагов
    else historyStep++;
}

function undoHistory() {
    if (historyStep > 0) {
        historyStep--;
        let state = textHistory[historyStep];
        let ta = document.getElementById('p_text');
        ta.value = state.val;
        ta.selectionStart = state.start;
        ta.selectionEnd = state.end;
        ta.dispatchEvent(new Event('input')); // Обновляем превью
    }
}

// --- ИНИЦИАЛИЗАЦИЯ ---
window.onload = async () => {
    let config = await eel.get_config()();
    if (config.api_id) document.getElementById('api_id').value = config.api_id;
    if (config.api_hash) document.getElementById('api_hash').value = config.api_hash;
    if (config.bot_token) document.getElementById('bot_token').value = config.bot_token;
    if (config.bot_user) document.getElementById('bot_user').value = config.bot_user;
    
    setActiveZone('media_path');
    saveHistoryState(); // Исходное пустое состояние для Ctrl+Z
};

// --- НАВИГАЦИЯ ---
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tabId}`).classList.add('active');
    event.currentTarget.classList.add('active');
}

// --- НАСТРОЙКИ ---
async function saveSettings() {
    let data = {
        api_id: document.getElementById('api_id').value,
        api_hash: document.getElementById('api_hash').value,
        bot_token: document.getElementById('bot_token').value,
        bot_user: document.getElementById('bot_user').value,
    };
    let res = await eel.save_config(data)();
    showToast(res, "success");
}

// --- УВЕДОМЛЕНИЯ ---
function showToast(msg, type="info") {
    let container = document.getElementById('toast-container');
    let toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = msg;
    if(type === "success") toast.style.borderLeftColor = "#00e676";
    if(type === "error") toast.style.borderLeftColor = "#ff1744";
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 400); }, 3500);
}

// --- ПРОГРЕСС БАР ---
eel.expose(update_progress);
function update_progress(percent, text) {
    document.querySelector('.progress-container').style.display = 'block';
    document.getElementById('progress-bar').style.width = percent + '%';
    document.getElementById('progress-text').innerText = text;
}

// --- ПРЕВЬЮ И СОХРАНЕНИЕ ИСТОРИИ ---
document.getElementById('c_name').addEventListener('input', (e) => document.getElementById('prev-name').innerText = e.target.value || "Название");

let typeTimer;
document.getElementById('p_text').addEventListener('input', (e) => {
    let txt = e.target.value.replace(/\n/g, '<br>'); 
    document.getElementById('prev-text').innerHTML = txt || "Текст поста...";
    
    // Сохраняем состояние для Ctrl+Z через 500мс после остановки ввода
    clearTimeout(typeTimer);
    typeTimer = setTimeout(saveHistoryState, 500);
});

document.getElementById('btn1_t').addEventListener('input', updateBtns);
function updateBtns() {
    let t = document.getElementById('btn1_t').value;
    document.getElementById('prev-btns').innerHTML = t ? `<div>${t}</div>` : '';
}

// --- ФОРМАТИРОВАНИЕ ТЕКСТА ---
function formatText(tag) {
    saveHistoryState(); // Сохраняем перед изменением

    let ta = document.getElementById('p_text');
    let start = ta.selectionStart;
    let end = ta.selectionEnd;
    let sel = ta.value.substring(start, end);
    let replacement = "";

    if (tag === 'a') {
        let url = prompt("Введите URL ссылки или юзернейм (с @):", "https://");
        if (!url) return;
        
        url = url.trim();
        // Автоматически чиним ссылку, если ввели юзернейм
        if (url.startsWith('@')) {
            url = "https://t.me/" + url.replace('@', '');
        } else if (!url.startsWith('http') && !url.startsWith('tg://')) {
            url = "https://" + url;
        }

        replacement = `<a href="${url}">${sel || 'текст ссылки'}</a>`;
    } else {
        replacement = `<${tag}>${sel}</${tag}>`;
    }

    ta.value = ta.value.substring(0, start) + replacement + ta.value.substring(end);
    
    // Возвращаем курсор на место
    if (sel.length === 0 && tag !== 'a') {
        ta.selectionStart = start + tag.length + 2; 
    } else {
        ta.selectionStart = start + replacement.length; 
    }
    
    ta.selectionEnd = ta.selectionStart;
    ta.focus();
    ta.dispatchEvent(new Event('input'));
    
    saveHistoryState(); // Сохраняем после изменения
}

// --- ГОРЯЧИЕ КЛАВИШИ (БИНДЫ) ---
document.getElementById('p_text').addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        let key = e.key.toLowerCase();
        
        // Массив кнопок для форматирования
        if (['b', 'i', 'u', 's', 'k', 'z'].includes(key)) {
            e.preventDefault(); // Отключаем стандартную функцию браузера

            if (key === 'z') {
                undoHistory(); // Откат
            } else {
                if (key === 'b') formatText('b'); // Жирный
                if (key === 'i') formatText('i'); // Курсив
                if (key === 'u') formatText('u'); // Подчеркнутый
                if (key === 's') formatText('s'); // Зачеркнутый (Ctrl+S)
                if (key === 'k') formatText('a'); // Ссылка (Ctrl+K)
            }
        }
    }
});

// --- DRAG & DROP и CTRL+V ДЛЯ КАРТИНОК ---
let activeDropZone = 'media_path'; 

function setActiveZone(zoneId) {
    activeDropZone = zoneId;
    document.querySelectorAll('.drop-zone').forEach(el => el.classList.remove('active-zone'));
    if(zoneId === 'avatar_path') document.getElementById('avatar-drop').classList.add('active-zone');
    if(zoneId === 'media_path') document.getElementById('media-drop').classList.add('active-zone');
}

document.getElementById('avatar-drop').addEventListener('click', () => setActiveZone('avatar_path'));
document.getElementById('media-drop').addEventListener('click', () => setActiveZone('media_path'));

async function browseFile(inputId) {
    let path = await eel.browse_file()();
    if (path) applyFileToPreview(inputId, path, "file:///" + path);
}

document.querySelectorAll('.drop-zone').forEach(zone => {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', e => { zone.classList.remove('dragover'); });
    zone.addEventListener('drop', e => {
        e.preventDefault(); zone.classList.remove('dragover');
        let file = e.dataTransfer.files[0];
        let targetId = zone.id.includes('avatar') ? 'avatar_path' : 'media_path';
        setActiveZone(targetId);
        if (file) handleDroppedFile(file, targetId);
    });
});

window.addEventListener('paste', e => {
    let items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (let index in items) {
        let item = items[index];
        if (item.kind === 'file') {
            let blob = item.getAsFile();
            handleDroppedFile(blob, activeDropZone); 
            e.preventDefault();
        }
    }
});

async function pasteFromClipboardBtn(targetId, event) {
    event.stopPropagation();
    setActiveZone(targetId);
    try {
        const items = await navigator.clipboard.read();
        for (let item of items) {
            const imageTypes = item.types.filter(type => type.startsWith('image/'));
            if (imageTypes.length > 0) {
                const blob = await item.getType(imageTypes[0]);
                const file = new File([blob], "pasted_image.png", { type: imageTypes[0] });
                handleDroppedFile(file, targetId);
                return;
            }
        }
        showToast("В буфере нет картинки!", "error");
    } catch (err) {
        showToast("Просто выдели зону и нажми Ctrl+V", "info");
    }
}

function handleDroppedFile(file, inputId) {
    let reader = new FileReader();
    reader.onload = async function(e) {
        let b64 = e.target.result;
        let savedPath = await eel.save_file_from_b64(b64, file.name)();
        applyFileToPreview(inputId, savedPath, b64);
        showToast(inputId === "avatar_path" ? "Аватар загружен" : "Медиа загружено", "success");
    };
    reader.readAsDataURL(file);
}

function applyFileToPreview(inputId, osPath, browserUrl) {
    document.getElementById(inputId).value = osPath;
    if (inputId === 'avatar_path') {
        document.querySelector('.ph-avatar').style.backgroundImage = `url('${browserUrl}')`;
        document.getElementById('avatar-drop').querySelector('p').innerText = "Аватар установлен!";
    } else {
        let m = document.getElementById('prev-media');
        m.style.display = 'block';
        m.style.backgroundImage = `url('${browserUrl}')`;
        document.getElementById('media-drop').querySelector('p').innerText = "Медиа установлено!";
    }
}

// --- ЗАПУСК ---
async function startProcess() {
    let apiData = {
        api_id: document.getElementById('api_id').value,
        api_hash: document.getElementById('api_hash').value,
        bot_token: document.getElementById('bot_token').value,
        bot_user: document.getElementById('bot_user').value
    };
    if (!apiData.api_id) return showToast("Заполните настройки API!", "error");

    let reacs =[];
    document.querySelectorAll('.reactions-box input:checked').forEach(cb => reacs.push(cb.value));

    let channelData = {
        name: document.getElementById('c_name').value,
        user: document.getElementById('c_user').value,
        bio: document.getElementById('c_bio').value,
        avatar_path: document.getElementById('avatar_path').value,
        reactions: reacs
    };

    let postData = {
        text: document.getElementById('p_text').value,
        media_path: document.getElementById('media_path').value,
        btns: [[document.getElementById('btn1_t').value, document.getElementById('btn1_u').value]]
    };

    document.querySelector('.progress-container').style.display = 'block';
    
    let res = await eel.run_process(apiData, channelData, postData)();
    
    if (res.status === "success") {
        showToast("Опубликовано! Ссылка в буфере обмена.", "success");
        update_progress(100, "Успешно завершено!");
    } else {
        showToast(res.msg, "error");
        update_progress(0, "Ошибка (см. уведомление)");
    }
}