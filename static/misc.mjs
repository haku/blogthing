async function checkFetchResp(resp) {
  if (resp.ok) return
  const body = await resp.text()  // TODO tidy / limit length / something
  throw new Error(`HTTP error ${resp.status}: ${body}`)
}

function formatTimestamp(timestamp) {
  const d = new Date(timestamp * 1000);
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${
      pad(d.getMonth() + 1)}-${
      pad(d.getDate())} ${
      pad(d.getHours())}:${
      pad(d.getMinutes())}:${
      pad(d.getSeconds())}`;
}

export { checkFetchResp, formatTimestamp }
