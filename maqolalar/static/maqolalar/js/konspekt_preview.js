document.addEventListener('DOMContentLoaded', function () {
    const textarea = document.getElementById('id_matn');
    if (!textarea) return;

    const panel = document.createElement('div');
    panel.innerHTML = `
        <h2 style="color:#c6a15a">Jonli ko‘rib chiqish</h2>
        <div id="konspekt-preview-result"
             style="background:#171717;color:#eee;padding:25px;
             border:1px solid #493b23;border-radius:8px;
             line-height:1.9;min-height:150px;overflow-wrap:anywhere">
             Natija shu yerda ko‘rinadi...
        </div>
    `;

    textarea.parentNode.appendChild(panel);

    const result = panel.querySelector('#konspekt-preview-result');
    let timer;

    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return '';
    }

    async function updatePreview() {
        result.textContent = 'Yuklanmoqda...';

        try {
            const response = await fetch('/konspekt-preview/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams({
                    matn: textarea.value
                })
            });

            if (!response.ok) throw new Error('Server xatosi');

            const data = await response.json();
            result.innerHTML = data.html || '<p>Hozircha matn yo‘q.</p>';
        } catch (error) {
            result.textContent = 'Ko‘rib chiqishni yuklashda xatolik.';
        }
    }

    textarea.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(updatePreview, 400);
    });

    updatePreview();
});
