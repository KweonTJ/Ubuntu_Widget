param([ValidateSet('Snapshot','PlayPause','Next','Previous')][string]$Action='Snapshot')
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
function Await($Operation,[Type]$Type) {
 $method=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1} | Select-Object -First 1
 $task=$method.MakeGenericMethod($Type).Invoke($null,@($Operation))
 if(-not $task.Wait(6000)){throw 'WinRT timeout'}
 return $task.Result
}
$result=@{media=@{status='unavailable'};bluetooth=@();foreground='';error=''}
try {
 Add-Type -AssemblyName System.Runtime.WindowsRuntime
 $null=[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager,Windows.Media.Control,ContentType=WindowsRuntime]
 $manager=Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
 $session=$manager.GetCurrentSession()
 if($null -ne $session) {
  if($Action -ne 'Snapshot') {
   $op=switch($Action){'PlayPause' {$session.TryTogglePlayPauseAsync()} 'Next' {$session.TrySkipNextAsync()} 'Previous' {$session.TrySkipPreviousAsync()}}
   $ok=Await $op ([bool]);@{ok=$ok}|ConvertTo-Json -Compress;exit 0
  }
  $properties=Await ($session.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
  $result.media=@{status='ready';title=$properties.Title;artist=$properties.Artist;playing=($session.GetPlaybackInfo().PlaybackStatus.ToString() -eq 'Playing');art=''}
  if($properties.Thumbnail) {
   try {
    $null=[Windows.Storage.Streams.DataReader,Windows.Storage.Streams,ContentType=WindowsRuntime]
    $stream=Await ($properties.Thumbnail.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
    if($stream.Size -gt 0 -and $stream.Size -le 2097152 -and $stream.ContentType -match '^image/(png|jpeg|webp|gif)$'){
     $reader=[Windows.Storage.Streams.DataReader]::new($stream)
     $loaded=Await ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
     $bytes=New-Object byte[] $loaded;$reader.ReadBytes($bytes)
     $result.media.art='data:'+$stream.ContentType+';base64,'+[Convert]::ToBase64String($bytes)
     $reader.Dispose()
    }
    $stream.Dispose()
   } catch { $result.media.art='' }
  }
 } else { $result.media=@{status='empty'} }
} catch { $result.error='media_unavailable' }
if($Action -ne 'Snapshot'){@{ok=$false}|ConvertTo-Json -Compress;exit 0}
try {
 Add-Type @'
using System;
using System.Runtime.InteropServices;
public class WidgetForeground {
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr window,out uint id);
}
'@
 [uint32]$processId=0
 $null=[WidgetForeground]::GetWindowThreadProcessId([WidgetForeground]::GetForegroundWindow(),[ref]$processId)
 if($processId -gt 0){$result.foreground=(Get-Process -Id $processId).ProcessName}
} catch {}
# Windows only exposes levels for some device/driver combinations.
try {
 $devices=Get-PnpDevice -Class Bluetooth -PresentOnly -ErrorAction SilentlyContinue | Where-Object {$_.Status -eq 'OK'}
 foreach($device in $devices){
  $connected=Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName 'DEVPKEY_Device_IsConnected' -ErrorAction SilentlyContinue
  if($connected.Data -ne $true){continue}
  $level=Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName '{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2' -ErrorAction SilentlyContinue
  if($null -ne $level.Data -and [int]$level.Data -ge 0 -and [int]$level.Data -le 100){$result.bluetooth+=@{name=$device.FriendlyName;percent=[int]$level.Data}}
 }
} catch {}
$result | ConvertTo-Json -Depth 6 -Compress
