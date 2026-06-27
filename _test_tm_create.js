const tm = require("E:/API获取工具/ZO注册/plugin/temp_mail");
(async () => {
  try {
    // Step 1: Create email
    const r = await tm.createEmail({ 
      providers: ["tempmailplus","guerrilla","maildrop","inboxes","catchmail","tempmailio"],
      log: console.log 
    });
    console.log(`\n=== Email: ${r.email} | Provider: ${r.provider} ===\n`);
    
    // Step 2: Show how to use in a real registration
    console.log("Ready to use this email for airport registration.");
    console.log(`Credentials: ${JSON.stringify(r.credentials)}`);
    
    // Step 3: Do a manual poll demo (show it can poll)
    console.log("\nDemo poll (showing current inbox)...");
    try {
      const msgs = await r.providerInstance.getMessages(r.credentials);
      console.log(`Inbox has ${msgs.length} messages`);
      msgs.forEach(m => console.log(`  - [${m.from}] ${m.subject}`));
    } catch(e) {
      console.log(`Poll demo: ${e.message}`);
    }
    
    // Save for browser test
    const fs = require("fs");
    fs.writeFileSync(
      __dirname + "/_last_temp_mail.json",
      JSON.stringify({ email: r.email, provider: r.provider, credentials: r.credentials, time: new Date().toISOString() }, null, 2)
    );
    console.log("\nSaved to _last_temp_mail.json");
    
  } catch(e) {
    console.error("FAIL:", e.message);
  }
})();
