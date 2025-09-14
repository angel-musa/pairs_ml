from ib_insync import IB, Stock, util

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=11)  # adjust port if not TWS Paper

contract = Stock('AAPL', 'SMART', 'USD')
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='3 Y',        # 3 years
    barSizeSetting='1 day',
    whatToShow='ADJUSTED_LAST',  # split/div adjusted
    useRTH=True,
    formatDate=1
)
print(len(bars), "bars")
df = util.df(bars)
print(df.head())
ib.disconnect()
