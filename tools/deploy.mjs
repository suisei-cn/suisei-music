import { env } from 'process'
import { writeFileSync } from 'fs'
import got from 'got'

function sleep(ms) {
  return new Promise((res) => {
    setTimeout(() => {
      res()
    }, ms)
  })
}

function buildSummary(summaryFilePath, result, success) {
  let lines = []
  lines.push(success ? '✅ Action **SUCCEEDED**.' : '❌ Action **FAILED**.')
  lines.push(['stdout:', '```', result.result.stdout, '```'].join('\n'))
  lines.push(['stderr:', '```', result.result.stderr, '```'].join('\n'))
  writeFileSync(summaryFilePath, lines.join('\n\n'))
}

;(async () => {
  const summaryFilePath = env.GITHUB_STEP_SUMMARY
  const url = new URL('https://suisei-podcast.outv.im/rpc')
  url.searchParams.set('key', env.BIN_API_KEY)
  url.searchParams.set('reason', `gh_${env.GITHUB_SHA}`)
  url.searchParams.set('action', 'fetch_clip')
  url.searchParams.set('delay', '1')

  const eventInfo = await got.post(String(url)).json()
  if (!eventInfo.ok) {
    console.error(`Failed: ${eventInfo.reason}`)
    process.exit(1)
  }

  const eventId = eventInfo.id
  const startDate = new Date()
  while (true) {
    await sleep(8000)
    if (Number(new Date()) - Number(startDate) > 25 * 60 * 1000) {
      console.error('Result fetching timeout.')
      writeFileSync(summaryFilePath, 'Action **TIMED-OUT**.')
      process.exit(1)
    }
    const eventResult = await got
      .get(`https://suisei-podcast.outv.im/status?id=${eventId}`)
      .json()
    switch (eventResult.cron.status) {
      case 'STARTED':
      case 'WAITING': {
        break
      }
      case 'FINISHED_OK': {
        buildSummary(summaryFilePath, eventResult.cron, true)
        process.exit(0)
        break
      }
      case 'FINISHED_BAD': {
        buildSummary(summaryFilePath, eventResult.cron, false)
        process.exit(1)
      }
      default: {
        console.error('Unrecognized status. Stop.')
        process.exit(1)
      }
    }
  }
})()
