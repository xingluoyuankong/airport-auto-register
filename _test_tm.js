const tm = require("E:/API获取工具/ZO注册/plugin/temp_mail");
(async () => {
  try {
    const r = await tm.createEmail({ providers: ["tempmailplus","guerrilla","maildrop","inboxes","catchmail","tempmailio"], log: console.log });
    console.log("OK|" + r.email + "|" + r.provider);
  } catch(e) {
    console.log("FAIL|" + e.message);
  }
})();
