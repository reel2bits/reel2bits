// This file have been imported from https://git.pleroma.social/pleroma/pleroma-fe

const fileSizeFormat = (num) => {
  var exponent
  var unit
  var units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  if (num < 1) {
    return num + ' ' + units[0]
  }

  exponent = Math.min(Math.floor(Math.log(num) / Math.log(1024)), units.length - 1)
  num = (num / Math.pow(1024, exponent)).toFixed(2) * 1
  unit = units[exponent]
  return { num: num, unit: unit }
}
const fileSizeFormatService = {
  fileSizeFormat
}
export default fileSizeFormatService
