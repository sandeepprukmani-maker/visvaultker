import { CodeEditor } from '../CodeEditor';

const sampleCode = `import { chromium } from 'playwright';

async function automateLogin() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.goto('https://example.com/login');
  await page.fill('#username', 'user@example.com');
  await page.fill('#password', 'password123');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('**/dashboard');
  console.log('Login successful!');
  
  await browser.close();
}

automateLogin();`;

export default function CodeEditorExample() {
  return (
    <div className="h-screen p-4">
      <CodeEditor 
        code={sampleCode} 
        language="typescript"
        onRun={() => console.log('Run automation')}
      />
    </div>
  );
}
