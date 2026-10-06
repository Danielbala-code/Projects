"""Private source ingestion and chronological SQL features; no raw rows in public output."""
import csv
import math
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SQL = (Path(__file__).parent/'queries.sql').read_text()


def ingest(path, con):
    con.executescript('DROP TABLE IF EXISTS lines; DROP TABLE IF EXISTS invoices; CREATE TABLE lines(invoice TEXT,customer TEXT,date TEXT,country TEXT,amount REAL);')
    seen=set();reasons=Counter();kept=[];dates=[];count=0
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            count+=1
            try:
                dt=datetime.strptime(row['InvoiceDate'],'%m/%d/%Y %H:%M')
                dates.append(dt)
            except (ValueError,TypeError):
                reasons['invalid_date']+=1;continue
            key=tuple(row.values())
            if key in seen:
                reasons['exact_duplicate']+=1;continue
            seen.add(key)
            invoice=row['InvoiceNo'].strip();customer=row['CustomerID'].strip()
            if invoice.upper().startswith('C'):
                reasons['cancellation']+=1;continue
            if not customer:
                reasons['missing_customer']+=1;continue
            try:
                quantity=float(row['Quantity']);price=float(row['UnitPrice'])
                if not math.isfinite(quantity*price):raise ValueError()
            except (ValueError,TypeError):
                reasons['invalid_numeric']+=1;continue
            if quantity<=0 or price<=0:
                reasons['nonpositive_amount']+=1;continue
            if not invoice or not customer.isdigit() or not row['Country'].strip():
                reasons['invalid_identity']+=1;continue
            kept.append((invoice,customer,dt.isoformat(sep=' '),row['Country'].strip(),quantity*price))
    con.executemany('INSERT INTO lines VALUES(?,?,?,?,?)',kept)
    conflict=con.execute('SELECT invoice FROM lines GROUP BY invoice HAVING COUNT(DISTINCT customer)>1 OR COUNT(DISTINCT date)>1 OR COUNT(DISTINCT country)>1').fetchall()
    con.execute('CREATE TABLE conflicts(invoice TEXT PRIMARY KEY)') if not con.execute("SELECT 1 FROM sqlite_master WHERE name='conflicts'").fetchone() else con.execute('DELETE FROM conflicts')
    con.executemany('INSERT INTO conflicts VALUES(?)',conflict)
    conflict_lines=con.execute('SELECT COUNT(*) FROM lines WHERE invoice IN (SELECT invoice FROM conflicts)').fetchone()[0]
    con.executescript('CREATE TABLE invoices AS SELECT invoice,customer,date,country,SUM(amount) AS amount FROM lines WHERE invoice NOT IN (SELECT invoice FROM conflicts) GROUP BY invoice,customer,date,country; CREATE INDEX invoice_customer_date ON invoices(customer,date); CREATE INDEX invoice_date ON invoices(date); DROP TABLE lines;')
    con.commit()
    return {'rows':count,'excluded':dict(reasons),'kept_lines':len(kept)-conflict_lines,'conflicting_invoices':len(conflict),'conflicting_lines':conflict_lines,'invoices':con.execute('SELECT COUNT(*) FROM invoices').fetchone()[0],'known_customers':con.execute('SELECT COUNT(DISTINCT customer) FROM invoices').fetchone()[0],'source_min_date':min(dates).isoformat(),'source_max_date':max(dates).isoformat(),'rule':'First matching reason; exact source-row deduplication is an assumption. Cancelled/returned and nonpositive lines excluded. Positive purchases do not measure net revenue.'}


def snapshot(con,cutoff,observed_end):
    end=cutoff+timedelta(days=30)
    if end>observed_end:raise ValueError('A complete 30-day outcome window is required.')
    params={'cutoff':cutoff.isoformat(sep=' '),'start':(cutoff-timedelta(days=90)).isoformat(sep=' '),'end':end.isoformat(sep=' ')}
    cursor=con.execute(SQL,params);names=[c[0] for c in cursor.description]
    return [dict(zip(names,row)) for row in cursor]
