Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
foreach ($v in $synth.GetInstalledVoices()) {
    if ($v.VoiceInfo.Culture.Name -like "zh*") { $synth.SelectVoice($v.VoiceInfo.Name); break }
}
$root = "C:\Users\LYY\WorkBuddy\2026-10-17-10-20-29\assets\audio"
$lines = Get-Content -Path "$root\texts.txt" -Encoding UTF8
foreach ($line in $lines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $idx = $line.IndexOf("|")
    if ($idx -lt 0) { continue }
    $name = $line.Substring(0, $idx).Trim()
    $txt = $line.Substring($idx + 1)
    $out = Join-Path $root ($name + ".wav")
    $synth.SetOutputToWaveFile($out)
    $synth.Speak($txt)
    $synth.SetOutputToNull()
    Write-Host "SAVED $name"
}
Write-Host "PS_TTS_DONE"
