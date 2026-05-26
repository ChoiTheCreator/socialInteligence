// Stable Figma Plugin API script.
// Creates editable 16:9 employment slides grounded in the actual report outputs.
// Uses only Frame, Text, Rectangle, and Ellipse for lower plugin failure risk.

const BASE_W = 1024;
const BASE_H = 576;
const W = 1280;
const H = 720;
const SCALE = W / BASE_W;
const GAP = 110;
const DECK = 'Employment Report Deck';

const C = {
  bg: '#EEF2FF',
  card: '#FFFFFF',
  title: '#1A2642',
  body: '#34405E',
  muted: '#7080C0',
  line: '#D8E1FF',
  blue: '#4F73F5',
  blueDark: '#3155D6',
  blueSoft: '#DEE6FF',
  green: '#16A34A',
  greenSoft: '#DFF7EA',
  orange: '#F97316',
  orangeSoft: '#FFE8D7',
  red: '#EF4444',
  redSoft: '#FFE2E2',
  purple: '#7C5CF6',
  purpleSoft: '#ECE7FF',
  yellow: '#F59E0B',
  yellowSoft: '#FFF2CC',
};

const FONT = {
  regular: { family: 'Inter', style: 'Regular' },
  medium: { family: 'Inter', style: 'Medium' },
  bold: { family: 'Inter', style: 'Bold' },
};

function rgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return {
    r: ((n >> 16) & 255) / 255,
    g: ((n >> 8) & 255) / 255,
    b: (n & 255) / 255,
  };
}

function fill(hex, opacity) {
  return [
    {
      type: 'SOLID',
      color: rgb(hex),
      opacity: opacity === undefined ? 1 : opacity,
    },
  ];
}

async function loadFonts() {
  await figma.loadFontAsync(FONT.regular);
  await figma.loadFontAsync(FONT.medium);
  await figma.loadFontAsync(FONT.bold);
}

function lineCount(value) {
  return String(value).split('\n').length;
}

function text(parent, value, x, y, w, size, color, font, lineHeight, h, align) {
  const node = figma.createText();
  parent.appendChild(node);
  node.fontName = font || FONT.medium;
  node.characters = value;
  node.fontSize = size;
  node.lineHeight = {
    unit: 'PIXELS',
    value: lineHeight || Math.round(size * 1.35),
  };
  node.fills = fill(color || C.title);
  node.x = x;
  node.y = y;
  node.resize(
    w,
    h || lineCount(value) * (lineHeight || Math.round(size * 1.35)) + 6,
  );
  if (align) node.textAlignHorizontal = align;
  return node;
}

function rect(parent, x, y, w, h, color, radius, opacity) {
  const node = figma.createRectangle();
  parent.appendChild(node);
  node.x = x;
  node.y = y;
  node.resize(w, h);
  node.fills = fill(color, opacity);
  node.cornerRadius = radius || 0;
  return node;
}

function ellipse(parent, x, y, size, color, opacity) {
  const node = figma.createEllipse();
  parent.appendChild(node);
  node.x = x;
  node.y = y;
  node.resize(size, size);
  node.fills = fill(color, opacity);
  return node;
}

function frame(parent, name, x, y, w, h, color, radius) {
  const node = figma.createFrame();
  parent.appendChild(node);
  node.name = name;
  node.x = x;
  node.y = y;
  node.resize(w, h);
  node.fills = fill(color || C.card);
  node.cornerRadius = radius || 0;
  node.clipsContent = true;
  return node;
}

function bottomOfPage() {
  let bottom = 0;
  for (const node of figma.currentPage.children) {
    if ('y' in node && 'height' in node)
      bottom = Math.max(bottom, node.y + node.height);
  }
  return bottom;
}

function slide(index, name, startY) {
  const s = figma.createFrame();
  s.name = `${DECK} / Slide ${String(index).padStart(2, '0')} - ${name}`;
  s.x = (index - 1) * (W + GAP);
  s.y = startY;
  s.resize(W, H);
  s.fills = fill(C.bg);
  s.clipsContent = true;
  return s;
}

function scaleNodeTree(parent, scale) {
  if (!('children' in parent)) return;
  parent.children.forEach((child) => {
    child.x *= scale;
    child.y *= scale;
    child.resize(child.width * scale, child.height * scale);
    if ('cornerRadius' in child && typeof child.cornerRadius === 'number') {
      child.cornerRadius *= scale;
    }
    if (child.type === 'TEXT') {
      child.fontSize *= scale;
      if (child.lineHeight.unit === 'PIXELS') {
        child.lineHeight = {
          unit: 'PIXELS',
          value: child.lineHeight.value * scale,
        };
      }
    }
    scaleNodeTree(child, scale);
  });
}

function header(parent, eyebrow, title, subtitle) {
  text(parent, eyebrow, 58, 34, 420, 13, C.blue, FONT.bold, 18);
  text(parent, title, 58, 62, 860, 32, C.title, FONT.bold, 41, 92);
  if (subtitle)
    text(parent, subtitle, 58, 142, 740, 14, C.muted, FONT.medium, 21);
}

function footer(parent, source) {
  text(
    parent,
    source ||
      'Source: KOSIS 고용 관련 시도별 분기 통계, employment_inequality_policy_report.md',
    58,
    546,
    760,
    10,
    C.muted,
    FONT.medium,
    14,
  );
}

function bottomBar(parent, label, message) {
  rect(parent, 0, 406, BASE_W, 170, C.blue, 0);
  text(parent, label, 74, 430, 420, 13, C.card, FONT.bold, 18);
  text(parent, message, 74, 460, 820, 23, C.card, FONT.bold, 31);
}

function pill(parent, value, x, y, w, color, bg) {
  const p = frame(parent, 'Pill', x, y, w, 26, bg || C.blueSoft, 13);
  text(p, value, 0, 6, w, 11, color || C.blue, FONT.bold, 15, 16, 'CENTER');
  return p;
}

function metric(parent, x, y, w, title, value, note, color, bg) {
  const c = frame(parent, 'Metric', x, y, w, 92, bg || C.card, 14);
  text(c, title, 18, 14, w - 36, 12, color || C.blue, FONT.bold, 17);
  text(c, value, 18, 38, w - 36, 22, C.title, FONT.bold, 28);
  if (note) text(c, note, 18, 68, w - 36, 10, C.muted, FONT.medium, 14);
  return c;
}

function panel(parent, x, y, w, h, title, color) {
  const p = frame(parent, 'Panel', x, y, w, h, C.card, 16);
  rect(p, 26, 20, 42, 4, color || C.blue, 2);
  text(p, title, 26, 36, w - 52, 15, C.title, FONT.bold, 20);
  return p;
}

function hbar(parent, label, value, max, x, y, w, color, suffix) {
  text(parent, label, x, y + 1, 134, 12, C.title, FONT.bold, 17);
  rect(parent, x + 146, y, w, 18, C.line, 9);
  rect(parent, x + 146, y, Math.max(6, (value / max) * w), 18, color, 9);
  const maxX =
    typeof parent.width === 'number' ? parent.width - 76 : x + 156 + w;
  text(
    parent,
    `${value}${suffix || ''}`,
    Math.min(x + 156 + w, maxX),
    y - 1,
    72,
    12,
    color,
    FONT.bold,
    17,
  );
}

function vbar(parent, label, value, min, max, x, y, w, h, color) {
  const ratio = (value - min) / (max - min);
  const bh = Math.max(6, ratio * h);
  rect(parent, x, y, w, h, C.line, 8);
  rect(parent, x, y + h - bh, w, bh, color, 8);
  text(
    parent,
    label,
    x - 16,
    y + h + 8,
    w + 32,
    10,
    C.muted,
    FONT.medium,
    14,
    16,
    'CENTER',
  );
}

function tableHeader(parent, y, columns) {
  rect(parent, 24, y, parent.width - 48, 28, C.blueSoft, 0);
  columns.forEach((c) =>
    text(parent, c.label, c.x, y + 8, c.w, 10, C.blue, FONT.bold, 13),
  );
}

function miniRow(parent, y, label, value, color) {
  const valueW = 112;
  const valueX =
    typeof parent.width === 'number' ? parent.width - valueW - 24 : 234;
  const labelW = Math.max(88, valueX - 54);
  ellipse(parent, 26, y + 6, 9, color || C.blue);
  text(parent, label, 44, y, labelW, 12, C.title, FONT.bold, 17);
  text(
    parent,
    value,
    valueX,
    y,
    valueW,
    11,
    C.muted,
    FONT.medium,
    17,
    18,
    'RIGHT',
  );
  rect(parent, 24, y + 28, parent.width - 48, 1, C.line, 0);
}

function heatCell(parent, x, y, w, h, value, color) {
  const opacity = Math.max(0.14, Math.min(0.9, value / 100));
  rect(parent, x, y, w, h, color, 8, opacity);
  text(
    parent,
    String(Math.round(value)),
    x,
    y + 6,
    w,
    10,
    value > 55 ? C.card : C.title,
    FONT.bold,
    14,
    16,
    'CENTER',
  );
}

function miniTrendBars(parent, x, y, w, h, values, min, max, color) {
  const gap = 8;
  const barW = (w - gap * (values.length - 1)) / values.length;
  values.forEach((value, i) => {
    const ratio = (value - min) / (max - min);
    const barH = Math.max(6, ratio * h);
    rect(
      parent,
      x + i * (barW + gap),
      y + h - barH,
      barW,
      barH,
      color,
      5,
      0.82,
    );
  });
}

function slide01(startY) {
  const s = slide(1, '분석 메시지', startY);
  text(
    s,
    'Employment Inequality Analysis',
    62,
    44,
    520,
    14,
    C.blue,
    FONT.bold,
    18,
  );
  text(
    s,
    '지역 고용격차는\n단순한 고용률 차이가 아니다',
    62,
    86,
    650,
    42,
    C.title,
    FONT.bold,
    54,
  );
  text(
    s,
    '2016~2025 KOSIS 고용 데이터를 이용해 지역 삶의 질 격차를 만드는\n고용 구조와 정책 레버를 도출했다.',
    66,
    218,
    600,
    18,
    C.body,
    FONT.medium,
    27,
  );

  metric(
    s,
    66,
    306,
    194,
    '표면 지표',
    '0.7%p',
    '15~64세 고용률 격차',
    C.blue,
    C.card,
  );
  metric(
    s,
    282,
    306,
    194,
    '구조 지표',
    '9.5점',
    '고용 포용성 점수 격차',
    C.red,
    C.card,
  );
  metric(
    s,
    498,
    306,
    194,
    '정책 1순위',
    '34.2',
    '산업기반 우선순위 지수',
    C.green,
    C.card,
  );

  const map = frame(
    s,
    'Abstract Region Map',
    734,
    92,
    210,
    246,
    C.blueSoft,
    30,
  );
  ellipse(map, 42, 42, 58, C.orange, 0.9);
  ellipse(map, 96, 88, 82, C.blue, 0.9);
  ellipse(map, 150, 46, 48, C.green, 0.9);
  ellipse(map, 132, 154, 42, C.purple, 0.75);
  rect(map, 44, 204, 124, 10, C.blue, 5, 0.18);
  text(map, '17개 시도', 0, 118, 210, 20, C.card, FONT.bold, 26, 30, 'CENTER');

  bottomBar(
    s,
    'Thesis',
    '고용률은 거의 비슷하지만, 일자리 질·청년 정착·산업 기반에서\n지역 간 삶의 질 격차가 구조적으로 벌어진다.',
  );
  return s;
}

function slide02(startY) {
  const s = slide(2, '데이터 신뢰성', startY);
  header(
    s,
    'Research Design',
    '원자료 검증부터 시작한 고용 EDA',
    '보고서의 첫 근거는 데이터가 비교 가능한 상태인지 검증한 것이다.',
  );

  metric(
    s,
    58,
    178,
    198,
    '분석 기간',
    '2016~2025',
    '완전연도 40개 분기',
    C.blue,
    C.blueSoft,
  );
  metric(
    s,
    276,
    178,
    198,
    '지역 단위',
    '17개 시도',
    '전국 합계 제외',
    C.green,
    C.greenSoft,
  );
  metric(
    s,
    494,
    178,
    198,
    '원자료',
    '6개 CSV',
    'KOSIS 분기 통계',
    C.orange,
    C.orangeSoft,
  );
  metric(
    s,
    712,
    178,
    198,
    '대부분 결측',
    '0.00%',
    '성·연령 파일만 2.62%',
    C.purple,
    C.purpleSoft,
  );

  const p = panel(s, 58, 304, 908, 206, 'Raw dataset EDA diagnosis', C.blue);
  tableHeader(p, 76, [
    { label: '원자료', x: 34, w: 176 },
    { label: '행', x: 232, w: 44 },
    { label: '열', x: 292, w: 44 },
    { label: '결측률', x: 356, w: 66 },
    { label: '분기', x: 450, w: 56 },
    { label: '지역', x: 532, w: 48 },
    { label: '역할', x: 612, w: 220 },
  ]);
  const rows = [
    [
      '성별 경제활동인구 총괄',
      '54',
      '289',
      '0.00%',
      '41',
      '17',
      '핵심 성과·포용성',
    ],
    ['교육정도별 취업자', '126', '43', '0.00%', '41', '17', '고학력 산업 기반'],
    ['취업시간별 취업자', '252', '43', '0.00%', '41', '17', '근로시간 안정성'],
    ['연령별 취업자', '180', '43', '0.00%', '41', '17', '청년 정착 가능성'],
  ];
  rows.forEach((r0, i) => {
    const y = 114 + i * 25;
    text(p, r0[0], 34, y, 176, 11, C.title, FONT.bold, 15);
    text(p, r0[1], 232, y, 44, 11, C.body, FONT.medium, 15);
    text(p, r0[2], 292, y, 44, 11, C.body, FONT.medium, 15);
    text(p, r0[3], 356, y, 66, 11, C.green, FONT.bold, 15);
    text(p, r0[4], 450, y, 56, 11, C.body, FONT.medium, 15);
    text(p, r0[5], 532, y, 48, 11, C.body, FONT.medium, 15);
    text(p, r0[6], 612, y, 220, 11, C.body, FONT.medium, 15);
  });
  footer(s, 'Source: outputs/tables/eda/raw_eda_diagnosis.csv');
  return s;
}

function slide03(startY) {
  const s = slide(3, '분석 프레임워크', startY);
  header(
    s,
    'Evaluation Framework',
    '고용 여건 평가 기준을 먼저 세웠다',
    '보고서는 고용이 삶의 질에 영향을 주는 경로를 6개 차원으로 정의했다.',
  );

  const dims = [
    [
      '기초 고용 접근성',
      '고용률·15~64세 고용률·참가율·실업률',
      '구직 매칭·직업훈련',
      C.blue,
    ],
    [
      '여성 고용 참여',
      '여성 고용률·여성 참가율·성별 격차',
      '돌봄·경력복귀·유연근무',
      C.green,
    ],
    [
      '안정적 임금일자리',
      '임금·상용·임시일용·자영업 비중',
      '상용직·사회보험·복지',
      C.orange,
    ],
    [
      '청년 정착 일자리',
      '청년층·고령층 취업자 비중',
      '대학-기업·주거·첫 직장',
      C.purple,
    ],
    [
      '근로시간 안정성',
      '단시간·장시간 취업자 비중',
      '시간제 사각지대·선택권',
      C.blueDark,
    ],
    [
      '고학력·지역산업 기반',
      '대졸이상 취업자 비중',
      '전문직무·R&D·지역산업',
      C.red,
    ],
  ];
  dims.forEach((d, i) => {
    const x = 58 + (i % 2) * 454;
    const y = 178 + Math.floor(i / 2) * 104;
    const c = frame(s, 'Evaluation Dimension', x, y, 420, 82, C.card, 16);
    rect(c, 0, 0, 8, 82, d[3], 0);
    text(c, d[0], 24, 14, 190, 15, C.title, FONT.bold, 20);
    text(c, d[1], 24, 40, 250, 11, C.body, FONT.medium, 16);
    pill(
      c,
      d[2],
      286,
      26,
      108,
      d[3],
      d[3] === C.red
        ? C.redSoft
        : d[3] === C.orange
          ? C.orangeSoft
          : d[3] === C.green
            ? C.greenSoft
            : C.blueSoft,
    );
  });
  footer(s, 'Source: outputs/tables/eda/analysis_framework.csv');
  return s;
}

function slide04(startY) {
  const s = slide(4, 'EDA 추세', startY);
  header(
    s,
    'EDA Trend',
    '10년 추세는 ‘작은 고용률 차이’와 ‘큰 구조 격차’를 동시에 보여준다',
  );

  const trend = panel(
    s,
    58,
    172,
    540,
    266,
    '수도권-비수도권 추세 비교',
    C.blue,
  );
  rect(trend, 44, 72, 430, 1, C.line, 0);
  rect(trend, 44, 132, 430, 1, C.line, 0);
  rect(trend, 44, 192, 430, 1, C.line, 0);
  miniTrendBars(
    trend,
    58,
    78,
    178,
    110,
    [66.7, 67.2, 67.5, 67.4, 66.3, 67.0, 69.3, 69.8, 70.4, 70.2],
    66,
    71,
    C.blue,
  );
  miniTrendBars(
    trend,
    270,
    78,
    178,
    110,
    [66.0, 66.5, 66.3, 66.7, 66.1, 66.6, 68.0, 68.8, 68.9, 69.5],
    66,
    71,
    C.orange,
  );
  text(
    trend,
    '15~64세 고용률: 두 집단 모두 상승, 격차는 제한적',
    52,
    210,
    420,
    13,
    C.body,
    FONT.bold,
    18,
  );
  pill(trend, '수도권', 380, 34, 64, C.blue, C.blueSoft);
  pill(trend, '비수도권', 450, 34, 72, C.orange, C.orangeSoft);

  const gap = panel(s, 626, 172, 340, 266, '지역 간 불평등 range', C.red);
  hbar(gap, '고용률', 9.1, 68.1, 34, 86, 82, C.blue, '');
  hbar(gap, '여성고용', 18.9, 68.1, 34, 124, 82, C.green, '');
  hbar(gap, '안정일자리', 68.1, 68.1, 34, 162, 82, C.red, '');
  hbar(gap, '포용성점수', 34.5, 68.1, 34, 200, 82, C.orange, '');
  text(
    gap,
    '2025년 기준 최고-최저 범위.\n단일 고용률보다 일자리 질 지표에서 지역 차이가 훨씬 크다.',
    34,
    30,
    270,
    13,
    C.body,
    FONT.medium,
    18,
  );
  footer(
    s,
    'Source: outputs/tables/results/metro_gap.csv, inequality_trend.csv',
  );
  return s;
}

function slide05(startY) {
  const s = slide(5, '표면 지표의 함정', startY);
  header(
    s,
    'Key Evidence 01',
    '고용률만 보면 격차가 작아 보인다',
    '2025년 15~64세 고용률 평균은 수도권과 비수도권이 거의 비슷하다.',
  );

  metric(
    s,
    74,
    210,
    240,
    '수도권 15~64세 고용률',
    '70.2%',
    'employment_rate_15_64',
    C.blue,
    C.card,
  );
  metric(
    s,
    344,
    210,
    240,
    '비수도권 15~64세 고용률',
    '69.5%',
    'employment_rate_15_64',
    C.orange,
    C.card,
  );
  const c = frame(s, 'Gap Callout', 644, 178, 280, 182, C.card, 26);
  text(c, '0.7%p', 0, 34, 280, 48, C.blue, FONT.bold, 58, 68, 'CENTER');
  text(
    c,
    '표면 지표만 보면\n지역 고용격차는 작아 보인다.',
    42,
    112,
    196,
    16,
    C.title,
    FONT.bold,
    24,
    58,
    'CENTER',
  );

  bottomBar(
    s,
    'Interpretation Shift',
    '그래서 분석 질문을 ‘취업했는가’에서\n‘어떤 질의 일자리에 접근하는가’로 바꿔야 한다.',
  );
  return s;
}

function slide06(startY) {
  const s = slide(6, '구조 지표 반전', startY);
  header(
    s,
    'Key Evidence 02',
    '고용 포용성 점수는 격차를 다시 드러낸다',
    '여러 고용 feature를 결합하면 수도권과 비수도권의 질적 차이가 커진다.',
  );

  const p = panel(
    s,
    70,
    178,
    884,
    210,
    '2025 수도권-비수도권 주요 지표 차이',
    C.orange,
  );
  hbar(p, '포용성 점수', 9.5, 10, 38, 86, 260, C.red, '점');
  hbar(p, '임금근로자', 7.8, 10, 38, 124, 260, C.blue, '%p');
  hbar(p, '상용근로자', 7.3, 10, 38, 162, 260, C.green, '%p');
  hbar(p, '대졸이상', 6.5, 10, 450, 86, 190, C.purple, '%p');
  hbar(p, '청년층', 2.3, 10, 450, 124, 190, C.orange, '%p');
  hbar(p, '고령층', 6.0, 10, 450, 162, 190, C.red, '%p');
  text(
    p,
    '단순 고용률보다 임금근로·상용직·대졸이상·청년/고령 구조에서 더 큰 차이가 나타난다.',
    42,
    28,
    770,
    14,
    C.body,
    FONT.bold,
    20,
  );

  bottomBar(
    s,
    'Core Claim',
    '격차의 핵심은 일자리 수가 아니라\n커리어 경로와 안정성을 제공하는 지역 산업 구조다.',
  );
  return s;
}

function slide07(startY) {
  const s = slide(7, '정책 우선순위 산정', startY);
  header(
    s,
    'Priority Model',
    '정책 우선순위는 세 가지 근거를 결합했다',
    '2025년 격차, 10년 지속성, 종합점수와의 상관을 함께 사용했다.',
  );

  const formula = frame(s, 'Formula', 74, 174, 876, 72, C.card, 18);
  pill(formula, '2025 상하위 격차', 34, 22, 138, C.blue, C.blueSoft);
  text(formula, '+', 198, 22, 24, 20, C.muted, FONT.bold, 26, 28, 'CENTER');
  pill(formula, '10년 평균 격차', 242, 22, 124, C.green, C.greenSoft);
  text(formula, '×', 392, 22, 24, 20, C.muted, FONT.bold, 26, 28, 'CENTER');
  pill(formula, '종합점수 상관', 436, 22, 124, C.orange, C.orangeSoft);
  text(formula, '=', 586, 22, 24, 20, C.muted, FONT.bold, 26, 28, 'CENTER');
  pill(formula, '정책 우선순위 지수', 630, 22, 166, C.red, C.redSoft);

  const chart = panel(s, 74, 278, 520, 196, '정책 레버 우선순위 지수', C.blue);
  hbar(chart, '고학력·산업', 34.2, 34.2, 34, 76, 238, C.blue, '');
  hbar(chart, '청년 정착', 21.3, 34.2, 34, 112, 238, C.green, '');
  hbar(chart, '안정 임금', 18.0, 34.2, 34, 148, 238, C.orange, '');

  const table = panel(s, 626, 278, 324, 196, '상위 3개 근거 수치', C.green);
  tableHeader(table, 70, [
    { label: '레버', x: 30, w: 90 },
    { label: '격차', x: 138, w: 44 },
    { label: '10년', x: 194, w: 44 },
    { label: '상관', x: 250, w: 44 },
  ]);
  const rows = [
    ['산업', '41.6', '38.6', '.85'],
    ['청년', '41.0', '40.7', '.52'],
    ['안정', '27.3', '24.0', '.70'],
  ];
  rows.forEach((r0, i) => {
    const y = 108 + i * 28;
    text(table, r0[0], 30, y, 90, 12, C.title, FONT.bold, 16);
    text(table, r0[1], 138, y, 44, 12, C.body, FONT.medium, 16);
    text(table, r0[2], 194, y, 44, 12, C.body, FONT.medium, 16);
    text(table, r0[3], 250, y, 44, 12, C.blue, FONT.bold, 16);
  });
  footer(s, 'Source: outputs/tables/results/priority.csv');
  return s;
}

function slide08(startY) {
  const s = slide(8, '지역별 구조 진단', startY);
  header(
    s,
    'Regional Diagnosis',
    '지역별 취약 축은 다르게 나타났다',
    '같은 비수도권 안에서도 필요한 정책 패키지가 다르다.',
  );

  const heat = panel(
    s,
    56,
    168,
    600,
    316,
    '2025 지역별 정책 필요도 heatmap',
    C.purple,
  );
  const cols = [
    ['접근', C.blue],
    ['여성', C.green],
    ['안정', C.orange],
    ['청년', C.purple],
    ['시간', C.blueDark],
    ['산업', C.red],
  ];
  cols.forEach((c0, i) =>
    text(
      heat,
      c0[0],
      112 + i * 70,
      70,
      48,
      10,
      C.muted,
      FONT.bold,
      14,
      16,
      'CENTER',
    ),
  );
  const regions = [
    ['전남', [37, 32, 71, 97, 51, 83]],
    ['경북', [39, 37, 59, 91, 39, 69]],
    ['전북', [46, 36, 50, 87, 41, 65]],
    ['강원', [38, 27, 54, 85, 46, 70]],
    ['울산', [59, 83, 21, 55, 28, 52]],
    ['충남', [34, 44, 39, 64, 40, 68]],
    ['서울', [55, 39, 23, 31, 31, 19]],
  ];
  regions.forEach((r0, ri) => {
    const y = 96 + ri * 28;
    text(heat, r0[0], 34, y + 6, 52, 11, C.title, FONT.bold, 14);
    r0[1].forEach((v, ci) =>
      heatCell(heat, 112 + ci * 70, y, 46, 22, v, cols[ci][1]),
    );
  });

  const call = panel(s, 688, 168, 280, 316, '지역별 1순위 처방', C.orange);
  miniRow(call, 80, '전남·경북 외', '청년 정착', C.purple);
  miniRow(call, 124, '충남·충북', '산업 기반', C.red);
  miniRow(call, 168, '울산', '여성 고용', C.green);
  miniRow(call, 212, '대구·부산 외', '기초 접근', C.blue);
  text(
    call,
    '결론: 전국 단일 처방보다\n지역별 병목을 겨냥해야 한다.',
    30,
    258,
    220,
    15,
    C.title,
    FONT.bold,
    22,
  );
  footer(s, 'Source: outputs/tables/results/region_recommendations.csv');
  return s;
}

function slide09(startY) {
  const s = slide(9, '정책 패키지', startY);
  header(
    s,
    'Policy Proposal',
    '고학력·청년정착형 안정일자리 패키지',
    '보고서의 최종 제안은 1순위 레버를 단독 추진하지 않고 세 축을 묶는 것이다.',
  );

  const pillars = [
    [
      '01',
      '고학력·지역산업 기반',
      '전략산업, 공공서비스, 보건·돌봄,\n디지털 전환, 제조 고도화, R&D',
      C.blue,
    ],
    [
      '02',
      '청년 정착 일자리',
      '지역 대학-기업 채용 경로,\n첫 직장, 경력 성장, 주거 지원',
      C.purple,
    ],
    [
      '03',
      '안정적 임금일자리',
      '상용직 전환, 사회보험,\n중소기업 임금·복지 격차 완화',
      C.green,
    ],
  ];
  pillars.forEach((p, i) => {
    const x = 64 + i * 302;
    const c = frame(s, 'Policy Pillar', x, 206, 260, 152, C.card, 24);
    rect(c, 0, 0, 260, 9, p[3], 0);
    pill(
      c,
      p[0],
      24,
      26,
      42,
      p[3],
      p[3] === C.green
        ? C.greenSoft
        : p[3] === C.purple
          ? C.purpleSoft
          : C.blueSoft,
    );
    text(c, p[1], 24, 66, 210, 19, C.title, FONT.bold, 25);
    text(c, p[2], 24, 104, 212, 13, C.body, FONT.medium, 19);
  });

  bottomBar(
    s,
    'Final Recommendation',
    '단순 일자리 수 확대보다, 지역에 남을 수 있는\n전문직무·청년 경로·상용직 기반을 함께 설계해야 한다.',
  );
  return s;
}

function slide10(startY) {
  const s = slide(10, '결론과 한계', startY);
  header(
    s,
    'Conclusion & Limits',
    '데이터가 말하는 결론과 해석 한계',
    '정책 효과 추정이 아니라 고용 구조 데이터가 가리키는 우선 개입 방향이다.',
  );

  const left = panel(s, 64, 176, 420, 226, '최종 결론', C.blue);
  miniRow(left, 78, '지역 고용격차의 핵심', '고용률보다 구조', C.blue);
  miniRow(left, 118, '최우선 정책 레버', '고학력·산업 기반', C.red);
  miniRow(left, 158, '보완 레버', '청년 정착 + 안정일자리', C.green);
  text(
    left,
    '전국 공통 일자리 수 확대보다\n취약 지역의 핵심 병목을 겨냥하는 방식이 타당하다.',
    28,
    194,
    350,
    13,
    C.title,
    FONT.bold,
    18,
  );

  const right = panel(s, 540, 176, 420, 226, '해석 한계', C.orange);
  miniRow(right, 78, '삶의 만족도 원자료', '직접 결합 X', C.orange);
  miniRow(right, 118, '인과 효과 추정', '정책 효과 아님', C.red);
  miniRow(right, 158, '청년·고령 비중', '인구구조 영향', C.purple);
  miniRow(right, 198, '2026년', '1분기 참고값', C.blue);

  bottomBar(
    s,
    'Closing Message',
    '이번 고용 파트는 ‘어디에 일자리가 많은가’가 아니라\n‘어디에 남을 만한 일자리 구조가 있는가’를 분석했다.',
  );
  return s;
}

async function main() {
  try {
    await loadFonts();
    const startY = bottomOfPage() + 180;
    const frames = [
      slide01(startY),
      slide02(startY),
      slide03(startY),
      slide04(startY),
      slide05(startY),
      slide06(startY),
      slide07(startY),
      slide08(startY),
      slide09(startY),
      slide10(startY),
    ];
    frames.forEach((frameNode) => scaleNodeTree(frameNode, SCALE));
    figma.currentPage.selection = frames;
    figma.viewport.scrollAndZoomIntoView(frames);
    figma.closePlugin('Created employment report deck.');
  } catch (err) {
    console.error(err);
    figma.notify(
      'Plugin error: ' + String(err && err.message ? err.message : err),
      {
        error: true,
        timeout: 9000,
      },
    );
    figma.closePlugin();
  }
}

main();
