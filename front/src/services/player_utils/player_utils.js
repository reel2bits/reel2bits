const secondsTimeSpanToMS = (s) => {
  if (isNaN(s)) {
    return '00:00'
  }
  var m = Math.floor(s / 60) // Get remaining minutes
  s -= m * 60
  s = Math.floor(s)
  return (m < 10 ? '0' + m : m) + ':' + (s < 10 ? '0' + s : s) // zero padding on minutes and seconds
}

const playerUtils = {
  secondsTimeSpanToMS
}

export default playerUtils
