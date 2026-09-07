import { app } from "../../scripts/app.js";

const PALETTE_ID = "kjranyone-irodoritts-emoji-palette";

const EMOJI_ITEMS = [
    { emoji: "👂", label: "囁き", description: "耳元の音" },
    { emoji: "😮‍💨", label: "吐息", description: "溜息、寝息" },
    { emoji: "⏸️", label: "間", description: "沈黙" },
    { emoji: "🤭", label: "笑い", description: "くすくす、含み笑い" },
    { emoji: "🥵", label: "喘ぎ", description: "うめき声、唸り声" },
    { emoji: "📢", label: "エコー", description: "リバーブ" },
    { emoji: "😏", label: "からかう", description: "甘えるように" },
    { emoji: "🥺", label: "震え声", description: "自信なさげに" },
    { emoji: "🌬️", label: "息切れ", description: "荒い息遣い、呼吸音" },
    { emoji: "😮", label: "息をのむ", description: "Gasp" },
    { emoji: "👅", label: "舐める音", description: "咀嚼音、水音" },
    { emoji: "💋", label: "リップノイズ", description: "Lip smack" },
    { emoji: "🫶", label: "優しく", description: "Tenderly" },
    { emoji: "😭", label: "泣き声", description: "嗚咽、悲しみ" },
    { emoji: "😱", label: "悲鳴", description: "叫び、絶叫" },
    { emoji: "😪", label: "眠そう", description: "気だるげに" },
    { emoji: "😴", label: "寝言", description: "いびき" },
    { emoji: "⏩", label: "早口", description: "一気に、急いで" },
    { emoji: "📞", label: "電話越し", description: "スピーカー越し" },
    { emoji: "🐢", label: "ゆっくり", description: "Slowly" },
    { emoji: "🥤", label: "飲み込む", description: "唾を飲む音" },
    { emoji: "🤧", label: "咳・鼻", description: "咳き込み、鼻すすり" },
    { emoji: "😒", label: "舌打ち", description: "Tutting" },
    { emoji: "😰", label: "慌てる", description: "動揺、緊張、どもり" },
    { emoji: "😆", label: "喜び", description: "嬉しそうに" },
    { emoji: "💥", label: "勢いよく", description: "力強い勢い" },
    { emoji: "😠", label: "怒り", description: "不満げ、拗ねる" },
    { emoji: "😲", label: "驚き", description: "感嘆" },
    { emoji: "🥱", label: "あくび", description: "Yawn" },
    { emoji: "😖", label: "苦しげ", description: "Agonizingly" },
    { emoji: "😟", label: "心配", description: "不安そうに" },
    { emoji: "🫣", label: "照れ", description: "恥ずかしそうに" },
    { emoji: "🙄", label: "呆れ", description: "Exasperatedly" },
    { emoji: "😊", label: "楽しげ", description: "嬉しそうに" },
    { emoji: "😎", label: "得意げ", description: "自信ありげに" },
    { emoji: "👌", label: "相槌", description: "頷く音" },
    { emoji: "🙏", label: "懇願", description: "お願いするように" },
    { emoji: "🥴", label: "酔う", description: "Drunkenly" },
    { emoji: "🎵", label: "鼻歌", description: "Humming" },
    { emoji: "🤐", label: "口を塞ぐ", description: "Muffled" },
    { emoji: "😌", label: "安堵", description: "満足げに" },
    { emoji: "🤔", label: "疑問", description: "Questioning" },
    { emoji: "💪", label: "力強く", description: "力を込めて" },
    { emoji: "👃", label: "嗅ぐ音", description: "匂いを嗅ぐ音" },
    { emoji: "📖", label: "朗読", description: "ナレーション" },
];

const PANEL_STYLE = {
    position: "fixed",
    right: "16px",
    bottom: "56px",
    zIndex: 100000,
    display: "none",
    flexDirection: "column",
    gap: "6px",
    maxWidth: "372px",
    padding: "8px",
    background: "var(--comfy-menu-bg, #353535)",
    color: "var(--input-text, #ddd)",
    border: "1px solid var(--border-color, #666)",
    borderRadius: "8px",
    boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
};

const BUTTON_STYLE = {
    position: "fixed",
    right: "16px",
    bottom: "12px",
    zIndex: 100000,
    width: "34px",
    height: "34px",
    padding: "0",
    fontSize: "18px",
    lineHeight: "1",
    cursor: "pointer",
    background: "var(--comfy-input-bg, #222)",
    color: "var(--input-text, #ddd)",
    border: "1px solid var(--border-color, #666)",
    borderRadius: "8px",
};

function applyStyle(el, style) {
    Object.assign(el.style, style);
}

function insertEmoji(target, emoji) {
    const text = target.value || "";
    const focused = document.activeElement === target;
    const start =
        focused && typeof target.selectionStart === "number"
            ? target.selectionStart
            : text.length;
    const end =
        focused && typeof target.selectionEnd === "number"
            ? target.selectionEnd
            : text.length;
    target.value = text.slice(0, start) + emoji + text.slice(end);
    const caret = start + emoji.length;
    target.focus({ preventScroll: true });
    try {
        target.setSelectionRange(caret, caret);
    } catch (error) {
        // selection is not supported on some input types
    }
    target.dispatchEvent(new Event("input", { bubbles: true }));
    target.dispatchEvent(new Event("change", { bubbles: true }));
}

function findEditableTarget() {
    const el = document.activeElement;
    if (el && (el.tagName === "TEXTAREA" || el.tagName === "INPUT")) {
        return el;
    }
    return null;
}

function buildPalette() {
    const panel = document.createElement("div");
    panel.id = PALETTE_ID;
    applyStyle(panel, PANEL_STYLE);

    const header = document.createElement("div");
    applyStyle(header, {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "8px",
        fontSize: "12px",
        opacity: "0.85",
    });
    const title = document.createElement("span");
    title.textContent = "IrodoriTTS Emoji Palette (45)";
    const close = document.createElement("button");
    close.textContent = "✕";
    applyStyle(close, {
        cursor: "pointer",
        background: "transparent",
        border: "none",
        color: "inherit",
        fontSize: "12px",
    });
    close.addEventListener("click", () => {
        panel.style.display = "none";
    });
    header.append(title, close);

    const hint = document.createElement("div");
    hint.textContent = "テキスト欄にカーソルを合わせて絵文字をクリック";
    applyStyle(hint, { fontSize: "11px", opacity: "0.6" });

    const grid = document.createElement("div");
    applyStyle(grid, {
        display: "grid",
        gridTemplateColumns: "repeat(7, 40px)",
        gap: "4px",
        maxHeight: "220px",
        overflowY: "auto",
    });

    for (const item of EMOJI_ITEMS) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = item.emoji;
        btn.title = `${item.emoji} ${item.label}: ${item.description}`;
        applyStyle(btn, {
            width: "40px",
            height: "34px",
            fontSize: "18px",
            lineHeight: "1",
            cursor: "pointer",
            background: "var(--comfy-input-bg, #222)",
            color: "inherit",
            border: "1px solid transparent",
            borderRadius: "6px",
        });
        btn.addEventListener("mouseenter", () => {
            btn.style.border = "1px solid var(--border-color, #888)";
        });
        btn.addEventListener("mouseleave", () => {
            btn.style.border = "1px solid transparent";
        });
        btn.addEventListener("click", () => {
            const target = findEditableTarget();
            if (target) {
                insertEmoji(target, item.emoji);
            } else {
                hint.textContent = "先にテキスト入力欄をクリックしてカーソルを合わせてください";
                applyStyle(hint, { color: "#f66", opacity: "1" });
                setTimeout(() => {
                    hint.textContent = "テキスト欄にカーソルを合わせて絵文字をクリック";
                    applyStyle(hint, { color: "", opacity: "0.6" });
                }, 2000);
            }
        });
        grid.appendChild(btn);
    }

    panel.append(header, hint, grid);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && panel.style.display === "flex") {
            panel.style.display = "none";
        }
    });
    return panel;
}

app.registerExtension({
    name: "kjranyone.IrodoriTTS.EmojiPalette",
    setup() {
        const panel = buildPalette();

        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.title = "IrodoriTTS Emoji Palette";
        toggle.textContent = "😀";
        applyStyle(toggle, BUTTON_STYLE);
        toggle.addEventListener("click", () => {
            const visible = panel.style.display === "flex";
            panel.style.display = visible ? "none" : "flex";
        });

        document.body.append(panel, toggle);
    },
});
