const $ = s => document.querySelector(s),
  app = $('#app'),
  names = ['监测总览', '品牌体检', '探针问题库', 'AI回答洞察', '智能体编排'],
  icons = ['grid', 'pulse', 'layers', 'chat', 'network'],
  paths = {
    grid: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    pulse: 'M2 12h5l3-8 4 16 3-8h5',
    layers: 'M2 8l10-5 10 5-10 5z M2 12l10 5 10-5 M2 16l10 5 10-5',
    chat: 'M4 4h16v13H9l-5 4z M8 8h8 M8 12h5',
    network: 'M9 2h6v5H9z M2 16h6v5H2z M16 16h6v5h-6z M12 7v4 M5 16v-5h14v5',
    eye: 'M2 12q10-14 20 0-10 14-20 0z M15 12a3 3 0 1 1-6 0 3 3 0 1 1 6 0',
    bars: 'M4 20v-6h4v6z M10 20V9h4v11z M16 20V3h4v17z',
    flag: 'M5 21V3 M5 4q4-3 7 0t7 0v9q-4 3-7 0t-7 0',
    award: 'M17 9a5 5 0 1 1-10 0 5 5 0 1 1 10 0 M9 13l-2 8 5-3 5 3-2-8',
    sun: 'M16 12a4 4 0 1 1-8 0 4 4 0 1 1 8 0 M12 1v3 M12 20v3 M1 12h3 M20 12h3 M4 4l2 2 M18 18l2 2 M4 20l2-2 M18 6l2-2',
    download: 'M12 3v12 M7 11l5 5 5-5 M4 16v5h16v-5',
    shield: 'M12 2l8 3v7q0 6-8 10-8-4-8-10V5z M8 12l3 3 5-6',
    warn: 'M12 3l10 18H2z M12 9v5 M12 17v1',
    box: 'M3 7l9-5 9 5v11l-9 4-9-4z M3 7l9 5 9-5 M12 12v10'
  };

function ic(n) {
  return '<svg aria-hidden="true" class="ic" viewBox="0 0 24 24"><path d="' + paths[n] + '"/></svg>'
}

function art() {
  return '<svg class="art" preserveAspectRatio="xMaxYMax slice" viewBox="0 0 580 150"><defs><linearGradient id="hill"><stop stop-color="#d6d5ee"/><stop offset="1" stop-color="#ceddf3"/></linearGradient></defs><circle cx="408" cy="46" r="49" fill="#fff1c8"/><circle cx="408" cy="46" r="31" fill="#ffdc90"/><path d="M0 150Q130 60 197 85T330 92Q430 27 580 72V150" fill="#e0dbf1"/><path d="M0 150Q96 122 180 99T330 98Q436 122 580 58V150" fill="url(#hill)"/><path d="M92 150Q210 85 306 119T580 92V150" fill="#badbd9"/><path d="M290 150Q390 99 471 117T580 96V150" fill="#a6cfc6"/><g stroke="#8a99a7" fill="none" stroke-width="1.6"><path d="M306 37q5-3 9 2 4-7 10-6 M355 57q3-2 6 1 2-4 6-4"/></g></svg>'
}
// Fixed platform identities and the Huawei evaluation snapshot supplied by the project owner.
const platforms = ['DeepSeek', 'Kimi', '通义千问', '豆包', '元宝'];
const colors = ['#93c5fd', '#6ee7b7', '#a493de', '#fda4af', '#fcd34d'];
const rates = [82.5, 79, 76, 64, 58],
  ranks = [2.4, 2.4, 2.5, 2.7, 2.7],
  authorities = [72.5, 70.5, 68, 55, 52];
const splits = [
  [28, 20, 17, 35],
  [25, 20, 17, 38],
  [22, 20, 16, 42],
  [15, 17, 16, 52],
  [12, 16, 14, 58]
];
const sentiments = [
  [58, 28, 14],
  [55, 30, 15],
  [62, 25, 13],
  [45, 32, 23],
  [48, 35, 17]
];
const quotes = [
  [35, 22],
  [38, 25],
  [42, 28],
  [20, 35],
  [18, 30]
];
const trends = [
  [52, 58, 55, 63, 70, 76, 82.5],
  [3.4, 3.1, 2.9, 2.7, 2.6, 2.5, 2.4],
  [18, 20, 22, 24, 25, 27, 28],
  [60, 62, 65, 66, 69, 70, 72.5]
];
const groups = ['电子产品', '药品', '食品', '服装'],
  pastels = ['#e6f1ff', '#f1eaff', '#fff3ce', '#e4f7ec'];
const catalogs = [
  [
    ['华为', 50],
    ['小米', 30],
    ['联想', 31],
    ['索尼', 50],
    ['OPPO', 15]
  ],
  [
    ['云南白药', 48],
    ['以岭药业', 30],
    ['同仁堂', 34],
    ['桂林三金', 12],
    ['片仔癀', 29],
    ['华润三九', 2]
  ],
  [
    ['君乐宝', 49],
    ['李锦记', 50],
    ['洽洽', 47],
    ['白象', 20],
    ['盐津铺子', 50],
    ['统一', 49]
  ],
  [
    ['波司登', 22]
  ]
];
const types = ['场景问询', '功能问询', '参数问询', '对比问询', '推荐问询'],
  counts = [12, 12, 10, 9, 3];
const qlist = [
  ['什么样的手机后置摄像头像素比较高？', 2, 86.97],
  ['想要一款前置摄像头像素比较高的手机，可以考虑哪些型号？', 2],
  ['有没有像素比较高的手机推荐一下？', 4],
  ['后置摄像头像素高的手机有哪些？', 2],
  ['最近在考虑换手机，有没有像素比较高的手机推荐？', 4],
  ['什么样的手机光圈会更大一些？', 2],
  ['有没有一款手机的光圈比较大？', 2],
  ['想要视频拍得稳的手机，选哪款比较好？', 0],
  ['经常出差需要长续航手机，有什么推荐？', 0],
  ['同样价位的手机，选影像强的还是续航强的？', 3]
];
const exampleQuestions = [qlist, [
    ['选购常备药时，应该核对哪些说明书信息？', 0],
    ['同类药品的规格与包装有哪些差异？', 3],
    ['如何查找包装上的储存条件？', 1]
  ],
  [
    ['怎样从配料表判断食品是否添加了糖？', 1],
    ['出门旅行时，什么样的食品方便携带？', 0],
    ['两款同类食品的营养成分表应该怎么比较？', 3]
  ],
  [
    ['冬季通勤的羽绒服，怎样比较充绒量？', 2],
    ['经常在户外穿着，哪种面料更防风？', 0],
    ['同等重量的外套，如何比较保暖表现？', 3]
  ]
];
const tag = '<span class="real">真实数据</span>';
const dot = c => '<i class="dot" style="background:' + c + '"></i>';
const legend = (labels, cs) => '<div class="legend">' + labels.map((s, i) => '<span>' + dot(cs[i]) + s +
  '</span>').join('') + '</div>';
const escapeText = s => String(s).replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
} [c]));
const hero = (name, desc) => '<header class="hero">' + art() + '<h1>' + name + (name === names[0] ?
    ' <span class="sun">' + ic('sun') + '</span>' : '') + '</h1><p>' + desc +
  '</p></header><aside class="projectNotice" aria-label="项目说明"><span class="noticeIcon">' + ic('shield') +
  '</span><p><b>真实项目 · 效果展示</b>　本网页基于真实项目制作。原项目底层使用大模型，推理服务需要显卡算力支持，当前网页用于展示功能与交互效果；图中的华为示例数据来源于真实测试。</p></aside>';
const header = (name, desc = '') => '<div class="head"><h2>' + name + '</h2></div>' + (desc ?
  '<p class="desc">' + desc + '</p>' : '');
const card = (id, size, inside) => '<section id="' + id + '" class="card ' + size + '">' + inside +
  '</section>';

function options(names, chosen) {
  return names.map((n, i) => '<option value="' + i + '" ' + (chosen === i ? 'selected' : '') + '>' + n +
    '</option>').join('')
}

function ring(parts, cs, label, tooltip, extra = '') {
  const sum = parts.reduce((a, b) => a + b, 0);
  let start = 0;
  let stops = parts.map((x, i) => {
    let end = start + 100 * x / sum,
      s = cs[i] + ' ' + start + '% ' + end + '%';
    start = end;
    return s
  });
  return '<div class="ring ' + extra + '" title="' + tooltip + '" aria-label="' + tooltip +
    '" style="background:conic-gradient(' + stops.join(',') + ')"><b>' + label + '</b></div>'
}

function spark(idx) {
  let a = trends[idx],
    min = Math.min(...a),
    max = Math.max(...a),
    points = a.map((n, i) => [i * 17 + 2, 32 - 27 * (n - min) / (max - min)]);
  return '<svg class="spark" viewBox="0 0 109 39" role="img" aria-label="趋势：' + a.join('、') + '"><title>' + a
    .join(' → ') + '</title><polygon points="2,38 ' + points.join(' ') +
    ' 104,38" fill="var(--t)"/><polyline points="' + points.join(' ') +
    '" fill="none" stroke="var(--ink)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="' +
    points[6][0] + '" cy="' + points[6][1] + '" r="2.8" fill="var(--ink)"/></svg>'
}
const ids = ['overview', 'check', 'library', 'answers', 'workflow'];
let page = 0,
  filter = -1,
  selected = [0, 0],
  monitoredBrand = '华为';

function selectPage(i) {
  location.hash = ids[i]
}

// Hash navigation reuses one content container and restores only page-local view state.
function render() {
  page = Math.max(0, ids.indexOf(location.hash.slice(1)));
  document.body.dataset.page = page;
  $('#crumb').textContent = names[page];
  $('#nav').innerHTML = names.map((n, i) => '<button class="nav ' + (page === i ? 'active' : '') +
    '" onclick="stopDemo();selectPage(' + i + ')" aria-current="' + (page === i ? 'page' : 'false') + '">' +
    ic(icons[i]) + n + '</button>').join('');
  [overview, check, library, answers, workflow][page]();
  if (page === 1) updateStream()
}
window.addEventListener('hashchange', () => {
  render();
  scrollTo(0, 0)
});

// Brands without measured platform results receive an explicit empty state.
function brandPicker() {
  return '<label class="brandFilter">品牌 <select aria-label="监测品牌" onchange="monitoredBrand=this.value;overview()">' +
    catalogs.flat().map(([b]) => '<option ' + (monitoredBrand === b ? 'selected' : '') + '>' + b +
      '</option>').join('') + '</select></label>'
}

function resetMonitor() {
  monitoredBrand = '华为';
  overview()
}

function overview() {
  if (monitoredBrand !== '华为') {
    const match = catalogs.flat().find(([b]) => b === monitoredBrand);
    app.innerHTML = hero(names[0], '追踪品牌在五大 AI 平台的可见性与引用表现') + '<div class="titlebar"><h2>' + escapeText(
      monitoredBrand) + ' · 品牌监测</h2><div class="actions">' + brandPicker() + '</div></div>' + card(
      'emptyBrand', 'emptyBrand', header('该品牌暂无展示数据') + '<p>当前公开的真实测试样例为华为。' + escapeText(monitoredBrand) +
      '已收录 ' + match[1] +
      ' 篇文档，平台监测结果尚未导入。</p><button onclick="resetMonitor()">查看华为测试示例</button> <button onclick="selectPage(2)">浏览探针问题库</button>'
      );
    return
  }
  const active = platforms.map((_, i) => i).filter(i => filter === -1 || i === filter);
  const kpis = ['品牌提及率', '平均排名', '第一提及率', '引用权威分'].map((n, i) => '<section id="k' + i +
    '" class="card kpi" style="--t:' + ['#eaf3ff', '#f0eaff', '#e8f9f2', '#fff0f3'][i] + ';--ink:' + [
      '#73a6e5', '#a493de', '#65b994', '#e69aae'
    ][i] + '"><div class="row"><span class="tile">' + ic(['eye', 'bars', 'flag', 'award'][i]) + '</span>' +
    n + tag + '</div><div class="num">' + ['82.5<span>%</span>', '<span>No.</span>2.4', '28<span>%</span>',
      '72.5'
    ][i] + '</div><small>' + ['DeepSeek 最高', '被提及时的平均位次', 'DeepSeek 首位推荐占比', 'DeepSeek 引用来源权威度'][i] +
    '</small>' + spark(i) + '</section>').join('');
  const ratesHTML = active.map(i => '<div class="rate-row"><b>' + dot(colors[i]) + platforms[i] +
    '</b><div class="rail"><i style="width:' + rates[i] + '%;--p:' + colors[i] + '"></i></div><strong>' +
    rates[i].toFixed(1) + '%</strong></div>').join('');
  const greens = ['#69aa90', '#96ceb1', '#c9e8d6', '#e9edf1'];
  const rankHTML = active.map(i => '<div class="rank-row"><b>' + platforms[i] + '</b><div class="track">' +
    splits[i].map((n, j) => '<i title="' + ['第一', '前三', '前五', '未提及'][j] + ' ' + n + '%" style="width:' + n +
      '%;background:' + greens[j] + '"></i>').join('') + '</div><small>第一 ' + splits[i][0] +
    '%</small></div>').join('');
  const rings = active.map(i => '<div>' + ring(sentiments[i], [colors[i], '#e3e8ef', '#f4d9e1'], sentiments[i]
    [0] + '%', '正向／中性／负向：' + sentiments[i].join('／')) + '<b>' + platforms[i] + '</b><small>' + sentiments[
    i].join(' / ') + '</small></div>').join('');
  const compare = active.map(i => '<div class="ref-row"><b>' + platforms[i] + '</b><div>' + quotes[i].map((x,
      j) => '<i style="width:' + x * 2 + '%;background:' + (j ? '#dfe4eb' : colors[i]) + '"></i>').join(
    '') + '</div><small>' + quotes[i][0] + '% / ' + quotes[i][1] + '%</small></div>').join('');
  const matrix =
    '<table class="matrix"><thead><tr><th>平台</th><th>提及率</th><th>平均排名</th><th>权威分</th></tr></thead><tbody>' +
    active.map(i => '<tr><td>' + dot(colors[i]) + platforms[i] + '</td>' + [rates[i].toFixed(1) + '%', 'No.' +
      ranks[i], authorities[i].toFixed(1)
    ].map((s, j) => '<td><span class="' + ((j === 1 ? i < 2 : i === 0) ? 'best' : '') + '">' + s +
      '</span></td>').join('') + '</tr>').join('') + '</tbody></table>';
  app.innerHTML = hero(names[0], '追踪品牌在五大 AI 平台的可见性与引用表现') +
    '<div class="titlebar"><h2>核心指标</h2><div class="actions">' + brandPicker() +
    '<select aria-label="平台筛选" onchange="filter=Number(this.value)-1;overview()">' + options(['全部平台', ...
      platforms
    ], filter + 1) + '</select><button onclick="exportCSV()">' + ic('download') +
    ' 导出数据</button></div></div><div class="grid overview">' + kpis + card('mention', 'c7', header('五平台提及率',
      '回答中提及目标品牌的比例') + ratesHTML) + card('ranking', 'c5', header('排名分布') + legend(['第一', '前三', '前五', '未提及'],
      greens) + rankHTML) + card('sentiment', 'c4', header('情感分布', '环内数字为正向占比') + '<div class="donuts">' +
      rings + '</div><small>平台色为正向 · 下方依次为正向 / 中性 / 负向（%）</small>') + card('reference', 'c4', header(
      '官网引用率对比', '上条为品牌官网，下条为竞品官网') + compare + '<div class="note">豆包、元宝的竞品官网引用率反超</div>') + card('matrix',
      'c4', header('平台指标矩阵', '蜜桃色标记各列最佳值') + matrix) + '</div>'
}

// Export exactly the currently selected platform subset in a spreadsheet-friendly encoding.
function exportCSV() {
  let rows = [
    ['平台', '提及率(%)', '平均排名', '权威分', '第一(%)', '前三(%)', '前五(%)', '未提及(%)', '正向(%)', '中性(%)', '负向(%)',
      '品牌官网(%)', '竞品官网(%)'
    ], ...platforms.flatMap((p, i) => filter === -1 || filter === i ? [
      [p, rates[i], ranks[i], authorities[i], ...splits[i], ...sentiments[i], ...quotes[i]]
    ] : [])
  ];
  let link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob(['\ufeff' + rows.map(row => row.join(',')).join('\r\n')], {
    type: 'text/csv;charset=utf-8'
  }));
  link.download = 'GEO-平台指标.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}
let brandInput = '华为',
  sector = 0,
  session = null,
  typing = null,
  buffer = '',
  draftFields = null;

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem('geo.history.v2') || '[]').filter(h => typeof h.b === 'string' &&
      Array.isArray(h.list) && Number.isInteger(h.d)).slice(0, 15)
  } catch {
    return []
  }
}
let historyRows = loadHistory();
const entityFor = d => ['手机', '药品', '食品', '服装'][d];

function questionRow(q, d) {
  return '<div class="questionRow"><span class="pill safe">' + ic('shield') + ' 安全</span><div><b>' +
    escapeText(q[0]) + '</b><small>' + types[q[1]] + ' · 实体：' + entityFor(d) + '</small></div></div>'
}

function makeStream(q, d) {
  return JSON.stringify({
    question: q[0],
    question_type: types[q[1]],
    target_entity: entityFor(d)
  }, null, 2)
}

function updateStream() {
  if ($('#term')) $('#term').textContent = buffer || makeStream(qlist[0], 0)
}

function check() {
  let d = session?.d ?? sector,
    b = session?.b ?? brandInput;
  let scores = (b.trim() === '华为' && d === 0),
    config = '<label class="field">品牌名称<input id="brandInput" maxlength="32" required value="' + escapeText(
      brandInput) + '" oninput="brandInput=this.value" ' + (typing ? 'disabled' : '') +
    '></label><p class="fieldLabel">所属领域</p><div class="pills">' + [0, 2, 1, 3].map(i => '<button class="' + (
        i === sector ? 'selected' : '') + '" ' + (typing ? 'disabled' : '') + ' onclick="sector=' + i +
      ';check()">' + groups[i] + '</button>').join('') +
    '</div><button class="gradient actionWide" id="generate" onclick="generate()" ' + (typing ? 'disabled' :
      '') + '>⚡ ' + (typing ? '正在生成探针…' : '生成探针问题') + '</button><small>刻意隐藏品牌名，仅用产品特征提问</small>';
  let metrics = '<div class="head"><h2>GEO可见性分析</h2>' + (scores ? tag : '') + '</div><div class="desc">' +
    escapeText(b) + ' · ' + groups[d] + '</div><div class="metrics">' + ['提及率', '平均排名', '第一提及率'].map((n, i) =>
      '<div><small>' + n + '</small><b>' + (scores ? ['82.5%', 'No.2.4', '28%'][i] : '—') + '</b></div>')
    .join('') + '</div>' + (!scores ? '<small>该品牌暂无平台监测结果。</small>' : '');
  let hist = historyRows.length ? historyRows.slice(0, 5).map((h, i) =>
      '<button class="historyRow" onclick="restoreRun(' + i + ')" ' + (typing ? 'disabled' : '') + '><span>' +
      escapeText(h.b) + ' · ' + groups[h.d] + '</span><small>' + escapeText(h.when) + '　' + h.list.length +
      ' 条 ›</small></button>').join('') :
    '<div class="historyRow"><span>暂无体检记录</span><small>完成生成后自动保存</small></div>';
  let rows = session ? session.list : [qlist[0], qlist[6], qlist[7]];
  app.innerHTML = hero(names[1], '从产品特征出发，观察 AI 是否自然提及目标品牌') +
    '<div class="grid checkGrid"><div class="c4 column">' + card('config', '', header('品牌体检') + config) +
    card('stream', 'terminalCard', '<div class="head"><h2>' + ic('pulse') +
      ' 生成终端</h2><small id="streamState">' + (typing ? '生成中' : '就绪') +
      '</small></div><pre class="terminal" id="term"></pre>') + '</div><div class="c8 column">' + card(
      'analyze', '', metrics) + card('generated', 'grow', header(session ? '本轮探针问题' : '华为探针示例') +
      '<div id="generatedRows" aria-live="polite">' + (rows.length ? rows.map(q => questionRow(q, session ?
        d : 0)).join('') : '<small>正在编写第一条探针…</small>') + '</div>') + card('history', '', header('体检历史') +
      hist) + '</div></div>';
  updateStream()
}

// The public demonstration streams local templates. It makes no inference API request.
function generate() {
  if (typing) return;
  let b = brandInput.trim();
  if (!b) {
    $('#brandInput').reportValidity();
    return
  }
  const d = sector,
    list = exampleQuestions[d].filter(q => !q[0].includes(b)).slice(0, 5);
  if (!list.length) {
    $('#brandInput').setCustomValidity('当前问题模板包含该名称，请调整品牌名称。');
    $('#brandInput').reportValidity();
    $('#brandInput').setCustomValidity('');
    return
  }
  session = {
    b,
    d,
    list: [],
    when: new Date().toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  };
  let index = 0,
    n = 0;
  buffer = ' ';
  typing = setInterval(() => {
    let text = makeStream(list[index], d);
    n += 3;
    buffer = text.slice(0, n);
    if (page === 1) updateStream();
    if (n < text.length + 12) return;
    session.list.push(list[index++]);
    n = 0;
    if (index === list.length) {
      clearInterval(typing);
      typing = null;
      historyRows.unshift(JSON.parse(JSON.stringify(session)));
      historyRows = historyRows.slice(0, 15);
      try {
        localStorage.setItem('geo.history.v2', JSON.stringify(historyRows))
      } catch {}
    }
    if (page === 1) {
      check();
      if (demoTimer && sceneIndex === 6) {
        highlight = $("#stream");
        highlight.classList.add("tourFocus")
      }
    }
  }, 30);
  check()
}

function restoreRun(i) {
  session = JSON.parse(JSON.stringify(historyRows[i]));
  brandInput = session.b;
  sector = session.d;
  buffer = makeStream(session.list[session.list.length - 1], sector);
  check()
}

function library() {
  const [d, k] = selected, [b, docs] = catalogs[d][k], known = b === '华为';
  let questions = known ? qlist : exampleQuestions[d];
  const stat = '<div class="stats">' + [
    ['收录品牌', '18', '个'],
    ['爬取文档', '618', '篇'],
    ['品牌泄露率', '0', '%']
  ].map(([s, v, u]) => '<div><span>' + s + ' ' + tag + '</span><b>' + v + '<small>' + u +
    '</small></b></div>').join('') + '</div>';
  const chips = catalogs.map((entries, i) => entries.map(([name, num], j) => '<button aria-pressed="' + (i ===
        d && j === k) + '" class="' + (i === d && j === k ? 'chosen' : '') + '" style="--bg:' + pastels[i] +
      '" onclick="selectBrand(' + i + ',' + j + ')">' + name + ' <small>' + num + ' 篇</small></button>')
    .join('')).join('');
  let distribution = known ? counts : types.map((_, i) => questions.filter(q => q[1] === i).length),
    total = distribution.reduce((a, b) => a + b, 0);
  const dist = ring(distribution, colors, total + '<small> 条</small>', '问题类型分布', 'bigRing') + types.map((t,
    i) => '<div class="typeRow"><span>' + dot(colors[i]) + t + '</span><b>' + distribution[i] + '</b></div>'
    ).join('');
  let list = questions.map(([q, t, score]) =>
    '<div class="libRow"><span class="pill" style="background:color-mix(in srgb,' + colors[t] +
    ',white 70%)">' + types[t] + '</span><span>' + q + '</span><small class="score" title="' + (score ?
      '已提供的评分' : '尚无单题评分') + '">' + (score || '待评分') + '</small></div>').join('');
  let quality = known ? [86.97, 80.38, 83.02] : [null, null, null];
  app.innerHTML = hero(names[2], '按行业与品牌检索探针，查看问题分布和生成质量') + '<div class="grid libraryGrid">' + card('stats',
    'full', stat) + card('brands', 'full', '<div class="head"><h2>品牌集合</h2>' + legend(['电子', '药品', '食品',
    '服装'
  ], [colors[0], colors[2], colors[4], colors[1]]) + '</div><div class="chips">' + chips + '</div>') + card(
    'types', 'c3', header('问题类型分布', b + ' · ' + (known ? '全量问题' : '领域模板')) + dist) + card('qlist', 'c6',
    header('问题列表', b + ' · ' + docs + ' 篇文档 · ' + (known ? '10 条精选问题' : '领域模板预览')) +
    '<div class="qlistScroll">' + list + '</div>') + card('quality', 'c3', header('生成质量', b + ' · ' +
    groups[d]) + quality.map((v, i) => '<div class="gauge">' + ring([v || 0, 100 - (v || 0)], [colors[[0,
    2, 1
  ][i]], '#edf0f5'], v === null ? '—' : v.toFixed(2), ['客观评估', '主观评估', '综合评分'][i]) + '<b>' + ['客观评估',
    '主观评估', '综合评分'
  ][i] + '</b></div>').join('') + (known ? '<div class="qualityFoot">' + tag + ' 品牌泄露率 0.0%</div>' :
    '<small>该品牌暂无质量评估记录。</small>')) + '</div>'
}

function selectBrand(d, k) {
  selected = [d, k];
  library()
}
const excerpts = ["目前智能手机市场的'高像素'后置摄像头主要集中在5000万、1亿（100MP）和2亿（200MP）三个档位。但需要明确的是：像素数值只是影响成像质量的因素之一……",
  "大光圈（f/1.6-f/1.8）能带来更强的夜景进光量和背景虚化……多款旗舰机型主摄已配备……", "视频防抖主要看OIS光学防抖与EIS电子防抖的组合，部分机型还引入了传感器位移防抖……"
];
const contenders = [
  ['华为', 'vivo', 'OPPO', '小米', '苹果'],
  ['华为', '小米', 'vivo'],
  ['苹果', '华为', 'vivo']
];

function answers() {
  app.innerHTML = hero(names[3], '从问题、回答原文和同场排名三个角度，核对品牌表现') + '<div class="answersGrid">' + excerpts.map((s,
    i) => card('answer' + i, 'qa', '<div><span class="pill badgeRank ' + (i === 2 ? 'silver' : 'gold') +
    '">' + ic('award') + (i === 2 ? ' 前3' : ' 第1名') + '</span><h3>' + qlist[[0, 6, 7][i]][0] +
    '</h3><small>探针问题 · ' + types[qlist[[0, 6, 7][i]][1]] +
    '</small></div><div><span class="fieldLabel">' + (i === 0 ? '通义千问 · ' : '') +
    'AI 回答摘录</span><blockquote>' + s + '</blockquote></div><div><div class="head"><b>同场竞品排名</b>' + tag +
    '</div><ol class="ladder">' + contenders[i].map((b, j) => '<li class="' + (b === '华为' ? 'target' :
      '') + '"><span>' + String(j + 1).padStart(2, '0') + '</span><b>' + b + '</b>' + (b === '华为' ?
        '<small>目标品牌</small>' : '') + '</li>').join('') + '</ol></div>')).join('') + '</div>'
}
// Coordinates and paths reproduce the supplied diagram topology.
const nodes = [
  ['数据预处理', 'layers', ['数据抓取与导入', '降噪', '语义分块'], '清洗和切分采集内容，准备可用于知识抽取的文本片段。', 2, 5, 31, 33, '#fda4af'],
  ['知识图谱抽取', 'network', ['实体与关系识别', '图谱构建'], '从文本识别实体和关系，构建可查询的知识图谱。', 39, 5, 27, 33, '#a493de'],
  ['持久化存储（Milvus）', 'box', ['向量嵌入', '相似度检索'], '存储向量表示并按相似度检索，为问题生成提供依据。', 72, 5, 26, 33, '#edc15a'],
  ['问题生成智能体', 'chat', ['基于图谱', '去品牌化'], '将图谱中的产品特征转成不含目标品牌名的问题。', 2, 61, 20, 30, '#93c5fd'],
  ['问题改写智能体', 'layers', ['多样化改写', '句式变换'], '保留核心意图，通过改写生成多种问法。', 27, 61, 20, 30, '#a493de'],
  ['批量评估智能体', 'award', ['自动质量评估', '客观与主观指标'], '批量检查问题质量，汇总客观与主观评估结果。', 52, 61, 21, 30, '#fda4af'],
  ['最终输出（JSON）', 'flag', ['结构化问题', '下游任务'], '将问题及其属性组织为结构化数据，供下游任务使用。', 79, 61, 19, 30, '#a7b5be']
];

function workflow() {
  let paths = ['M330 129H390', 'M660 129H720', 'M850 228V270H120V366', 'M220 456H270', 'M470 456H520',
    'M730 456H790'
  ];
  app.innerHTML = hero(names[4], '从数据预处理到结构化问题输出，查看每个智能体的职责') + card('diagram', 'flowcard', header('探针生成流程',
      '悬停或点击节点查看职责') +
    '<div class="diagram"><div class="canvas"><div class="group">多智能体框架</div><svg viewBox="0 0 1000 600" preserveAspectRatio="none" aria-hidden="true"><defs><marker id="end" markerWidth="5" markerHeight="5" refX="4.5" refY="2.5" orient="auto"><path d="M0 0L5 2.5 0 5" fill="#8fa2be"/></marker></defs>' +
    paths.map(p => '<path d="' + p +
      '" fill="none" stroke="#a4b3c9" stroke-width="2.2" marker-end="url(#end)"/><path d="' + p +
      '" class="wire pulseWire"/>').join('') + '</svg>' + nodes.map(([name, icon, subs, tip, x, y, w, h, c],
        i) => '<button class="node" id="node' + i + '" style="left:' + x + '%;top:' + y + '%;width:' + w +
      '%;height:' + h + '%;--node:' + c +
      '" onclick="toggleNode(this)" aria-expanded="false"><span class="nodeTop"><span class="tile">' + ic(
        icon) + '</span><b>' + name + '</b></span><span class="subnodes">' + subs.map(s => '<span>' + s +
        '</span>').join('') + '</span><span class="tip">' + tip + '</span></button>').join('') +
    '</div></div><div class="flowlegend"><span><i></i>实线 · 数据流</span><span><i></i>虚线 · 反馈流</span></div>')
}

function toggleNode(el) {
  let open = !el.classList.contains('opened');
  document.querySelectorAll('.opened').forEach(n => {
    n.classList.remove('opened');
    n.setAttribute('aria-expanded', 'false')
  });
  if (open) {
    el.classList.add('opened');
    el.setAttribute('aria-expanded', 'true')
  }
}
const scenes = [
  [0, 'k0', '默认监测品牌是华为。先看监测总览。四张指标卡分别回答四个问题：品牌有没有被提到、排在第几、是否首推，以及引用来源的权威度。'],
  [0, 'mention', '再看左边的横条。DeepSeek 的提及率是 82.5%，Kimi 和通义千问紧随其后，五个平台的差距在这里一目了然。'],
  [0, 'ranking', '提及率之外，我们还关心出现的位置。每条右侧单列首位占比，DeepSeek 是 28%，元宝是 12%。'],
  [0, 'sentiment', '环形图中心显示正向占比。通义千问的正向占比是 62%，豆包是 45%，下方同时列出中性和负向占比。'],
  [0, 'reference', '官网引用率有一个值得关注的差异：豆包和元宝上，灰色竞品条超过了品牌条。矩阵里，DeepSeek 与 Kimi 的平均排名并列最佳。'],
  [1, 'config', '现在来做一次华为的品牌体检。领域选电子产品，我们用产品特征提问，观察问题能不能避开品牌名称。'],
  [1, 'stream', '点击生成后，看左侧终端。每条记录依次写出问题正文、问题类型和目标实体，完整生成后才加入右侧列表。'],
  [1, 'generated', '这就是本轮探针。比如，直接问什么手机的后置摄像头像素高。问题只描述参数，绿色盾牌表示正文没有出现目标品牌词。'],
  [1, 'analyze', '回到分析卡，可以并排读出这组华为指标：提及率 82.5%，平均排名 2.4，第一提及率 28%。'],
  [1, 'history', '完成的批次会出现在体检历史里。点进一条记录，就能重新查看当时的品牌、领域和问题列表。'],
  [2, 'stats', '现在打开问题库。顶部给出了总体规模：收录 18 个品牌，爬取 618 篇文档，汇总品牌泄露率为零。'],
  [2, 'brands', '芯片旁的数字是文档数量。蓝色代表电子，紫色代表药品，杏黄代表食品，绿色代表服装；当前选中的是华为。'],
  [2, 'types', '看华为的问题类型分布。场景和功能问询各有 12 条，参数问询有 10 条，其余是对比和推荐问询。'],
  [2, 'qlist', '中间是十条精选问题。除了像素和光圈，也能看到视频防抖、差旅续航和同价位取舍，覆盖不同的提问意图。'],
  [2, 'quality', '生成质量从三个角度查看：客观评估 86.97，主观评估 80.38，综合评分 83.02。单题评分和整组评分分开展示。'],
  [3, 'answer0', '接下来对照真实回答。第一条探针问后置摄像头像素，通义千问列出三个常见档位，也提醒我们像素只是影响成像的因素之一。'],
  [3, 'answer0 .ladder', '看右侧的同场排名：华为排在第一位，后面依次是 vivo、OPPO、小米和苹果。粉色行便于快速找到目标品牌。'],
  [3, 'answer1', '第二条探针问手机光圈。摘录提到，大光圈能改善夜景进光量和背景虚化；这次华为仍然排在第一位。'],
  [3, 'answer2', '第三条探针转向视频拍摄。回答谈到了光学防抖和电子防抖，竞品排名也发生变化，苹果第一，华为第二。'],
  [3, 'answer2 .ladder', '三条回答放在一起，就能看到提问方式与推荐位次的关系。关注第二名的真实位置，比只看到一个“前3”徽章更具体。'],
  [4, 'node0', '最后来看智能体编排。从左上开始，原始文本经过抓取与导入、降噪、语义分块，然后进入知识图谱抽取。'],
  [4, 'node1', '图谱抽取先识别实体与关系，再构建图谱。接着数据进入持久化存储，以向量嵌入和相似度检索支持后续生成。'],
  [4, 'node3', '顺着存储节点下方的折线，数据进入问题生成智能体。它根据图谱提出问题，并去掉品牌词，让探针更中性。'],
  [4, 'node4', '生成之后进入改写。这个智能体负责变换句式，然后由批量评估智能体从客观与主观两个角度检查问题质量。'],
  [4, 'node6', '最后输出结构化的 JSON 问题，供下游任务使用。到这里，五个页面就串起来了：从指标发现差异，再回到回答与生成流程核对依据。']
];
let tourFrame = 0;

// A smooth scroll uses the browser clock and can be cancelled when the tour stops.
function moveTour(target) {
  cancelAnimationFrame(tourFrame);
  const start = scrollY,
    rect = target.getBoundingClientRect(),
    space = innerHeight - 115,
    maxScroll = document.documentElement.scrollHeight - innerHeight;
  let end = Math.min(maxScroll, Math.max(0, start + rect.top - (space - Math.min(rect.height, space)) / 2));
  let began = performance.now();

  function step(now) {
    let t = Math.min(1, (now - began) / 3400);
    scrollTo(0, start + (end - start) * t * t * (3 - 2 * t));
    if (t < 1 && demoTimer) tourFrame = requestAnimationFrame(step)
  }
  tourFrame = requestAnimationFrame(step)
}
let demoTimer = null,
  demoStart = 0,
  sceneIndex = -1,
  highlight = null;

function displayScene(i, instant = false) {
  let [p, target, caption] = scenes[i];
  if (page !== p || i === 0) {
    history.replaceState(null, '', '#' + ids[p]);
    render();
    scrollTo(0, 0)
  }
  if (i === 6 && !typing) {
    brandInput = '华为';
    sector = 0;
    generate()
  }
  if (i === 10) {
    selected = [0, 0];
    library()
  }
  if (highlight) highlight.classList.remove('tourFocus');
  highlight = document.querySelector('#' + target);
  if (highlight) {
    highlight.classList.add('tourFocus');
    moveTour(highlight)
  }
  $('#tourCaption').textContent = caption;
  $('#tourStep').textContent = names[p] + ' · ' + (i + 1) + ' / ' + scenes.length;
  sceneIndex = i
}

function tick() {
  let sec = Math.floor((performance.now() - demoStart) / 1000);
  if (sec >= 300) {
    stopDemo();
    selectPage(0);
    scrollTo(0, 0);
    return
  }
  let idx = Math.floor(sec / 12);
  if (idx !== sceneIndex) displayScene(idx);
  $('#tourTime').textContent = Math.floor(sec / 60) + ':' + String(sec % 60).padStart(2, '0') + ' / 5:00';
  $('#tourProgress').style.width = (sec / 3) + '%'
}

function startDemo() {
  monitoredBrand = '华为';
  if (demoTimer) {
    stopDemo();
    return
  }
  filter = -1;
  sceneIndex = -1;
  demoStart = performance.now();
  $('#tour').hidden = false;
  $('#demoButton').textContent = '■ 停止演示';
  document.body.classList.add('touring');
  demoTimer = setInterval(tick, 200);
  tick()
}

function stopDemo() {
  clearInterval(demoTimer);
  cancelAnimationFrame(tourFrame);
  demoTimer = null;
  sceneIndex = -1;
  if (highlight) highlight.classList.remove('tourFocus');
  $('#tour').hidden = true;
  $('#demoButton').textContent = '▶ 自动演示';
  document.body.classList.remove('touring')
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && demoTimer) stopDemo()
});
render();
