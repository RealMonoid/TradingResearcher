// Fixed synthetic import/exploration/portfolio export in the owned empty database.
var ab = null, analysis = null;
function stage(text) { WScript.Echo("stage=" + text); }
try {
    var expected = WScript.Arguments(0);
    stage("connecting"); ab = new ActiveXObject("Broker.Application");
    var actual = String(ab.DatabasePath).replace(/\\+$/, "").toLowerCase();
    if (!expected || actual != expected.replace(/\\+$/, "").toLowerCase() || ab.Stocks.Count != 0)
        throw new Error("Expected empty owned database; refusing mutation");
    var count = Number(WScript.Arguments(6));
    if (count != 1 && count != 2) throw new Error("Invalid fixed synthetic inventory");
    stage("importing"); var imported = ab.Import(0, WScript.Arguments(1), WScript.Arguments(2));
    if (ab.Stocks.Count != count) throw new Error("Imported inventory differs");
    stage("checking_import"); for (var n = 0; n < count; n++) {
        var stock = ab.Stocks.Item(n);
        if ((stock.Ticker != "TRF_A" && stock.Ticker != "TRF_B") || stock.Quotations.Count != 8)
            throw new Error("Unexpected synthetic symbol or bar count");
    }
    stage("saving_database"); ab.SaveDatabase();
    stage("opening_analysis"); analysis = ab.AnalysisDocs.Open(WScript.Arguments(3));
    if (!analysis) throw new Error("Cannot open frozen analysis request");
    for (var action = 1; action <= 2; action++) {
        stage("starting_action_" + action);
        if (analysis.Run(action) != 1) throw new Error("Analysis did not start");
        var deadline = new Date().getTime() + 30000;
        while (analysis.IsBusy) {
            if (new Date().getTime() > deadline) { analysis.Abort(); throw new Error("Analysis timeout"); }
            WScript.Sleep(1000);
        }
        stage("exporting_action_" + action);
        if (analysis.Export(WScript.Arguments(action + 3), 0) != 1) throw new Error("Analysis export failed");
    }
    WScript.Echo("status=completed");
} catch (error) {
    WScript.Echo("error=" + error.number + ": " + error.message);
    if (analysis) { try { analysis.Close(); } catch (ignored) {} }
    WScript.Quit(1);
}
if (analysis) analysis.Close();
