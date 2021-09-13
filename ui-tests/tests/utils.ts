import { TestInfo } from '@playwright/test';

export async function timeit(fn: () => Promise<void>): Promise<string> {
  const start = performance.now();
  await fn();
  const end = performance.now();
  return Number((end - start) / 1000).toFixed(3);
}

export function average(arr: any[]): string {
  const aver =
    arr.reduce((p, c) => parseFloat(p) + parseFloat(c), 0) / arr.length;
  return aver.toFixed(3);
}

export async function addBenchmarkToTest(
  notebookName: string,
  testFunction: () => Promise<void>,
  testInfo: TestInfo,
  benchmarkTime = 1
): Promise<void> {
  const testTimeArray = [];
  for (let idx = 0; idx < benchmarkTime; idx++) {
    const testTime = await timeit(testFunction);
    console.log(notebookName, 'execution time:', testTime, ' s');
    testTimeArray.push(testTime);
    await new Promise(r => setTimeout(r, 500));
  }
  testInfo.attachments.push({
    name: notebookName,
    contentType: 'application/json',
    body: Buffer.from(JSON.stringify({ testTime: average(testTimeArray) }))
  });
}
