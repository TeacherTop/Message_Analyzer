import './style.css'

const apiUrl = 'http://127.0.0.1:8000'
const app = document.querySelector('#app')

app.innerHTML = `
  <main class="shell">
    <header class="topbar"><a class="brand" href="/">Диалоги<span> / аналитика</span></a><span class="privacy">Файл остаётся на этом компьютере</span></header>
    <section class="intro">
      <p class="eyebrow">АНАЛИЗ TELEGRAM-ПЕРЕПИСКИ</p>
      <h1>Увидеть больше<br>в привычных диалогах.</h1>
      <p class="lead">Загрузите JSON-экспорт Telegram: покажем ритм общения, активность участников и поведенческие группы диалогов.</p>
    </section>
    <form id="upload-form" class="upload-card">
      <label class="dropzone" for="chat-file"><span class="file-icon">↑</span><strong id="file-name">Выберите JSON-файл переписки</strong><small>Экспорт Telegram · .json</small><input id="chat-file" type="file" accept="application/json,.json" required></label>
      <div class="options"><label><input id="with-umap" type="checkbox" checked> Карта поведенческих кластеров</label><label><input id="with-topics" type="checkbox"> Семантические темы <span class="hint">дольше</span></label></div>
      <button id="submit" class="primary" type="submit">Проанализировать переписку <span>→</span></button>
      <p id="status" class="status" role="status"></p>
      <p class="config-note">Для анализа запусти локальный API командой <code>make api</code>. Данные не отправляются на Vercel.</p>
    </form>
    <section id="results" class="results" hidden></section>
    <footer>Ваш файл остаётся только на время обработки запроса.</footer>
  </main>`

const form = document.querySelector('#upload-form')
const fileInput = document.querySelector('#chat-file')
const status = document.querySelector('#status')
const button = document.querySelector('#submit')
const results = document.querySelector('#results')

fileInput.addEventListener('change', () => {
  document.querySelector('#file-name').textContent = fileInput.files[0]?.name || 'Выберите JSON-файл переписки'
})

form.addEventListener('submit', async (event) => {
  event.preventDefault()
  const file = fileInput.files[0]
  if (!apiUrl) {
    status.textContent = 'Сервис API пока не настроен. Добавьте VITE_API_URL в настройках Vercel.'
    status.className = 'status error'
    return
  }
  if (!file) return

  const params = new URLSearchParams({
    include_topics: String(document.querySelector('#with-topics').checked),
    include_umap: String(document.querySelector('#with-umap').checked),
  })
  const body = new FormData()
  body.append('file', file)
  button.disabled = true
  button.innerHTML = '<span class="spinner"></span> Анализируем…'
  status.textContent = 'На больших переписках анализ может занять несколько минут.'
  status.className = 'status'
  results.hidden = true

  try {
    const response = await fetch(`${apiUrl}/upload-chat?${params}`, {
      method: 'POST',
      body,
      targetAddressSpace: 'loopback',
    })
    const payload = await response.json()
    if (!response.ok) throw new Error(payload.detail || 'Не удалось обработать файл')
    renderResults(payload)
    status.textContent = 'Готово. Файл обработан.'
    status.className = 'status success'
  } catch (error) {
    status.textContent = error.message === 'Failed to fetch'
      ? 'Не удалось подключиться к локальному API. Запусти make api и разреши сайту доступ к локальной сети.'
      : error.message || 'Не удалось обработать файл.'
    status.className = 'status error'
  } finally {
    button.disabled = false
    button.innerHTML = 'Проанализировать переписку <span>→</span>'
  }
})

function renderResults(data) {
  const overview = data.overview || {}
  const messages = data.messages || {}
  const sessions = data.sessions || {}
  const activity = data.activity || {}
  const users = Object.entries(messages.messages_per_user || {}).sort((a, b) => b[1] - a[1])
  const maxUserCount = Math.max(1, ...users.map(([, count]) => count))
  const clusters = Object.entries(data.amount || {}).sort((a, b) => Number(a[0]) - Number(b[0]))
  const topics = Object.values(data.topics || {})
  const hours = Array.from({ length: 24 }, (_, hour) => [hour, activity.activity_by_hour?.[hour] || activity.activity_by_hour?.[String(hour)] || 0])
  const maxHourCount = Math.max(1, ...hours.map(([, count]) => count))
  const weekdays = Object.entries(activity.activity_by_weekday || {})
  const maxWeekdayCount = Math.max(1, ...weekdays.map(([, count]) => count))
  const weekdayNames = { Monday: 'Пн', Tuesday: 'Вт', Wednesday: 'Ср', Thursday: 'Чт', Friday: 'Пт', Saturday: 'Сб', Sunday: 'Вс' }

  results.innerHTML = `
    <div class="results-heading"><div><p class="eyebrow">РЕЗУЛЬТАТ АНАЛИЗА</p><h2>Общая картина</h2></div><button class="text-button" id="reset">Новый файл ↗</button></div>
    <div class="metrics">
      ${metric('Сообщений', format(overview.messages_total))}
      ${metric('Участников', format(overview.users_total))}
      ${metric('Диалоговых сессий', format(overview.sessions_total))}
      ${metric('Слов в сообщении', number(messages.avg_word_count))}
    </div>
    <div class="columns">
      <article class="panel"><p class="eyebrow">УЧАСТНИКИ</p><h3>Кто пишет чаще</h3><div class="bars">${users.map(([name, count]) => `<div class="bar-row"><div><span>${escapeHtml(name || 'Без имени')}</span><b>${format(count)}</b></div><i><span style="width:${Math.round(count / maxUserCount * 100)}%"></span></i></div>`).join('') || '<p class="muted">Нет данных</p>'}</div></article>
      <article class="panel"><p class="eyebrow">ДИАЛОГИ</p><h3>Как устроены сессии</h3><div class="facts"><div><span>В среднем сообщений</span><b>${number(sessions.avg_messages_per_session)}</b></div><div><span>Максимум в сессии</span><b>${format(sessions.max_messages_in_session)}</b></div><div><span>Средняя длительность</span><b>${duration(sessions.avg_session_duration_minutes)}</b></div><div><span>Чаще начинает</span><b>${escapeHtml(topEntry(sessions.session_starters))}</b></div></div></article>
    </div>
    <article class="panel"><p class="eyebrow">РИТМ ОБЩЕНИЯ</p><h3>Когда переписываются</h3><div class="activity-charts"><div><span class="chart-label">По часам</span><div class="hour-chart" role="img" aria-label="Активность сообщений по часам">${hours.map(([hour, count]) => `<span title="${hour}:00 · ${count} сообщ." style="height:${Math.max(3, Math.round(count / maxHourCount * 100))}%"></span>`).join('')}</div><div class="hour-labels"><span>00</span><span>06</span><span>12</span><span>18</span><span>24</span></div></div><div><span class="chart-label">По дням недели</span><div class="weekday-chart">${weekdays.map(([day, count]) => `<div><span>${weekdayNames[day] || escapeHtml(day)}</span><i><b style="width:${Math.round(count / maxWeekdayCount * 100)}%"></b></i><small>${format(count)}</small></div>`).join('')}</div></div></div></article>
    ${clusters.length ? `<article class="panel cluster-panel"><p class="eyebrow">ПОВЕДЕНЧЕСКИЕ КЛАСТЕРЫ</p><h3>Типы диалогов</h3><div class="cluster-list">${clusters.map(([id, count]) => `<div><span class="cluster-dot">${Number(id) + 1}</span><span>Группа ${Number(id) + 1}</span><b>${format(count)} сессий</b></div>`).join('')}</div></article>` : ''}
    ${data.umap_image ? `<article class="panel"><p class="eyebrow">КАРТА СХОДСТВА</p><h3>Сессии и их группы</h3><img class="umap" alt="Карта поведенческих кластеров" src="data:image/png;base64,${data.umap_image}"></article>` : ''}
    ${topics.length ? `<article class="panel"><p class="eyebrow">СЕМАНТИЧЕСКИЕ ТЕМЫ</p><h3>О чём говорят</h3><div class="topic-list">${topics.map((topic, index) => `<div><span>${String(index + 1).padStart(2, '0')}</span><p>${escapeHtml(topic.keywords || '')}</p><b>${format(topic.count)} сессий</b></div>`).join('')}</div></article>` : ''}`

  results.hidden = false
  results.scrollIntoView({ behavior: 'smooth', block: 'start' })
  document.querySelector('#reset').addEventListener('click', () => {
    results.hidden = true
    form.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function metric(label, value) { return `<article><span>${label}</span><strong>${value}</strong></article>` }
function format(value) { return Number(value || 0).toLocaleString('ru-RU') }
function number(value) { return Number.isFinite(Number(value)) ? Number(value).toLocaleString('ru-RU', { maximumFractionDigits: 1 }) : '—' }
function duration(value) { return value == null ? '—' : `${number(value)} мин` }
function topEntry(values) { const entry = Object.entries(values || {}).sort((a, b) => b[1] - a[1])[0]; return entry ? `${entry[0]} · ${entry[1]}` : '—' }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]) }
