import fileSizeFormatService from '../../../../../src/services/file_size_format/file_size_format.js'
describe('fileSizeFormat', () => {
  it('Formats file size', () => {
    const values = [1, 1024, 1048576, 1073741824, 1099511627776]
    const expected = [
      {
        num: 1,
        unit: 'B'
      },
      {
        num: 1,
        unit: 'KiB'
      },
      {
        num: 1,
        unit: 'MiB'
      },
      {
        num: 1,
        unit: 'GiB'
      },
      {
        num: 1,
        unit: 'TiB'
      }
    ]

    var res = []
    for (var value in values) {
      res.push(fileSizeFormatService.fileSizeFormat(values[value]))
    }
    expect(res).to.eql(expected)
  })
})
