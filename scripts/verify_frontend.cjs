/** Validate real inline scripts and pure import/grading functions without a UI.
 * Run from the repository root: node scripts/verify_frontend.cjs
 * No CDN access, browser profile, or real localStorage data is used.
 */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
let checks = 0;

function check(value, description) {
  // Count behaviors rather than echoing any application or session data.
  assert.ok(value, description);
  checks += 1;
}

function loadFunctions(filename) {
  // Compile every inline script, then omit only the UI initialization call.
  const html = fs.readFileSync(path.join(root, filename), 'utf8');
  const blocks = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
    .map(match => match[1]).filter(block => block.trim());
  assert.equal(blocks.length, 1, 'expected a single application script');
  new vm.Script(blocks[0], { filename });
  checks += 1;
  const marker = filename === 'index.html' ? '// 初始化' : '// ============ Init';
  const end = blocks[0].lastIndexOf(marker);
  assert.ok(end > 0, 'initialization boundary must be present');
  const store = new Map();
  const context = vm.createContext({
    console,
    localStorage: {
      getItem: key => store.get(key) ?? null,
      setItem: (key, value) => store.set(key, String(value)),
      removeItem: key => store.delete(key),
    },
  });
  new vm.Script(blocks[0].slice(0, end), { filename }).runInContext(context, { timeout: 2000 });
  return context;
}

function verifyParsing(context, filename) {
  // Test the sample readers will actually import, including all five types.
  const sample = fs.readFileSync(path.join(root, 'examples/questions.txt'), 'utf8');
  const questions = context.parseTextToQuestions(sample);
  check(questions.length === 5, `${filename}: import five example questions`);
  const types = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'short_answer'];
  types.forEach((type, index) => check(questions[index].type === type, `${filename}: infer ${type}`));
  check(questions.every(question => question.content && question.answer), `${filename}: retain stems and answers`);
  const rows = [{ 题目: 'Flask 使用哪种编程语言？', 题型: '单选', A: 'Python', B: 'SQL', 答案: 'A', 解析: 'Flask 是 Python 框架。' }];
  const excel = context.parseExcelRows(rows);
  check(excel.length === 1 && excel[0].answer === 'A' && excel[0].options.length === 2, `${filename}: map spreadsheet columns`);
  const duplicate = { type: 'short_answer', content: '重复题干测试', answer: '示例答案' };
  check(context.dedupeQuestions([duplicate, duplicate]).length === 1, `${filename}: deduplicate question content`);
}

function verifyGrading(context, filename) {
  // Match existing comparison semantics; no semantic or AI grading is claimed.
  check(context.isUserAnswerCorrect('A', { type: 'single_choice', answer: 'A' }), `${filename}: single choice`);
  check(context.isUserAnswerCorrect('C,A', { type: 'multiple_choice', answer: 'A,C' }), `${filename}: order-independent multiple choice`);
  check(!context.isUserAnswerCorrect('A', { type: 'multiple_choice', answer: 'A,C' }), `${filename}: reject partial multiple choice`);
  check(context.isUserAnswerCorrect('true', { type: 'true_false', answer: '正确' }), `${filename}: normalize true/false`);
  check(context.isUserAnswerCorrect(' JSON。 ', { type: 'short_answer', answer: 'json' }), `${filename}: normalize text answers`);
  check(!context.isUserAnswerCorrect('wrong', { type: 'fill_blank', answer: '4000' }), `${filename}: reject an incorrect fill answer`);
}

for (const filename of ['index.html', 'static/index.html']) {
  const context = loadFunctions(filename);
  verifyParsing(context, filename);
  verifyGrading(context, filename);
}
console.log(JSON.stringify({ checks_passed: checks, network_requests: 0, real_browser_data_touched: false }));
