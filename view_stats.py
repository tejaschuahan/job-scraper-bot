"""View database statistics"""
import sqlite3

conn = sqlite3.connect('jobs.db')
c = conn.cursor()

print('\n' + '=' * 50)
print('JOB DATABASE STATS')
print('=' * 50 + '\n')

total = c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
print(f'Total jobs in database: {total}\n')

print('Jobs per site:')
for row in c.execute('SELECT site, COUNT(*) FROM jobs GROUP BY site'):
    print(f'  {row[0]}: {row[1]}')

print(f'\nLatest 10 jobs:')
print('-' * 50)
for row in c.execute('SELECT title, company, site FROM jobs ORDER BY scraped_at DESC LIMIT 10'):
    print(f'  • {row[0][:50]}')
    print(f'    Company: {row[1]}')
    print(f'    Site: {row[2]}')
    print()

conn.close()
