import csv
from datetime import datetime
import sqlite3
import pytest
from audience.data import ingest, snapshot


def write_rows(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country'])
        writer.writerows(rows)


def test_cleaning_and_invoice_aggregation(tmp_path):
    a=['100','A','item',2,'6/30/2011 10:00',3,'1','United Kingdom']
    rows=[a,a,['100','B','other',1,'6/30/2011 10:00',4,'1','United Kingdom'],
          ['C101','A','return',-1,'7/2/2011 10:00',3,'1','United Kingdom'],
          ['102','A','unknown',1,'7/3/2011 10:00',3,'','United Kingdom'],
          ['103','A','bad',0,'7/3/2011 10:00',3,'1','United Kingdom']]
    p=tmp_path/'data.csv';write_rows(p,rows)
    con=sqlite3.connect(':memory:');audit=ingest(p,con)
    assert audit['rows']==6
    assert audit['excluded']=={'exact_duplicate':1,'cancellation':1,'missing_customer':1,'nonpositive_amount':1}
    assert con.execute('SELECT customer,amount FROM invoices').fetchall()==[('1',10.0)]
    assert audit['kept_lines']==2 and audit['invoices']==1


def test_features_do_not_see_future_and_window_is_complete(tmp_path):
    p=tmp_path/'data.csv'
    rows=[['100','A','item',1,'6/20/2011 10:00',10,'1','United Kingdom'],
          ['101','A','item',1,'7/1/2011 00:00',10000,'1','United Kingdom'],
          ['102','A','item',1,'8/5/2011 10:00',10,'2','United Kingdom']]
    write_rows(p,rows);con=sqlite3.connect(':memory:');ingest(p,con)
    first=snapshot(con,datetime(2011,7,1),datetime(2011,8,5))
    assert first[0]['frequency']==1 and first[0]['spend']==10
    assert first[0]['repeat']==1
    con.execute("UPDATE invoices SET amount=20000 WHERE invoice='101'")
    second=snapshot(con,datetime(2011,7,1),datetime(2011,8,5))
    assert first==second
    with pytest.raises(ValueError,match='complete'):
        snapshot(con,datetime(2011,8,1),datetime(2011,8,5))


def test_conflicting_invoice_is_quarantined(tmp_path):
    p=tmp_path/'data.csv'
    write_rows(p,[['100','A','item',1,'6/20/2011 10:00',10,'1','UK'],['100','B','item',1,'6/20/2011 10:00',10,'2','UK']])
    con=sqlite3.connect(':memory:');audit=ingest(p,con)
    assert audit['conflicting_invoices']==1 and audit['invoices']==0
