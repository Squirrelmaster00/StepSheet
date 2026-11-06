// Toolbar button: open the editor, or switch to it if it's already open.
const EDITOR = chrome.runtime.getURL("editor.html");
chrome.action.onClicked.addListener(async () => {
  const tabs = await chrome.tabs.query({ url: EDITOR });
  if (tabs.length) {
    await chrome.tabs.update(tabs[0].id, { active: true });
    await chrome.windows.update(tabs[0].windowId, { focused: true });
  } else {
    await chrome.tabs.create({ url: EDITOR });
  }
});
