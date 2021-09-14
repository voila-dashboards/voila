import { TestInfo } from '@playwright/test';
import { benchmark } from '@jupyterlab/galata';
export async function timeit(fn: () => Promise<void>): Promise<string> {
  const start = performance.now();
  await fn();
  const end = performance.now();
  return Number(end - start).toFixed(1);
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
  browserName: string,
  nSamples = 1
): Promise<void> {
  const testTimeArray = [];
  const attachmentCommon = {
    nSamples: nSamples,
    browser: browserName,
    file: `${notebookName}.ipynb`,
    project: testInfo.project.name
  };
  for (let idx = 0; idx < nSamples; idx++) {
    const testTime = await timeit(testFunction);
    console.log(notebookName, 'execution time:', testTime, 'ms');
    testTimeArray.push(testTime);
    testInfo.attachments.push(
      benchmark.addAttachment({
        ...attachmentCommon,
        test: 'Render',
        time: average(testTimeArray)
      })
    );
    await new Promise(r => setTimeout(r, 500));
  }
  // testInfo.attachments.push({
  //   name: notebookName,
  //   contentType: 'application/json',
  //   body: Buffer.from(JSON.stringify({ testTime: average(testTimeArray) }))
  // });
}
