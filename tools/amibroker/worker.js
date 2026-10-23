// Windows Script Host / JScript. External controller, never executed inside AFL.
var ab = null, analysis = null;
try {
    var action = WScript.Arguments(0);
    var expected = WScript.Arguments(1);
    ab = new ActiveXObject("Broker.Application");
    var actual = String(ab.DatabasePath).replace(/\\+$/, "").toLowerCase();
    if (expected && actual != expected.replace(/\\+$/, "").toLowerCase())
        throw new Error("Unexpected database; refusing any mutation");
    if (action == "quit") {
        if (!expected) throw new Error("Quit requires an owned database");
        ab.Quit();
    } else {
        WScript.Echo("version=" + ab.Version);
        WScript.Echo("database=" + ab.DatabasePath);
        WScript.Echo("stocks=" + ab.Stocks.Count);
        if (action == "smoke") {
            if (!expected || ab.Stocks.Count != 0) throw new Error("Smoke requires an empty owned database");
            var imported = ab.Import(0, WScript.Arguments(2), WScript.Arguments(3));
            WScript.Echo("import_result=" + imported);
            if (ab.Stocks.Count != 1 || ab.Stocks.Item("BTCUSDT_TEST").Quotations.Count != 96)
                throw new Error("Unexpected imported symbol/bar count");
            ab.SaveDatabase();
            analysis = ab.AnalysisDocs.Open(WScript.Arguments(4));
            if (!analysis || analysis.Run(1) != 1) throw new Error("Exploration did not start");
            var deadline = new Date().getTime() + 30000;
            while (analysis.IsBusy) {
                if (new Date().getTime() > deadline) {
                    analysis.Abort();
                    throw new Error("Exploration timeout");
                }
                WScript.Sleep(1000);
            }
            if (analysis.Export(WScript.Arguments(5), 0) != 1) throw new Error("Export failed");
            WScript.Echo("export=completed");
        } else if (action != "probe") throw new Error("Unknown action");
    }
} catch (error) {
    WScript.Echo("error=" + error.number + ": " + error.message);
    if (analysis) { try { analysis.Close(); } catch (ignored) {} }
    WScript.Quit(1);
}
if (analysis) analysis.Close();
