# CSS314 — Minimal Python Parallel Systems Lab (Ungraded)

Это **новое**, сокращённое практическое задание от 13.11.2026. Не используйте результаты и VERIFY_HASH из предыдущего 120-минутного лабораторного задания: экспериментальные размеры изменены.

## Система
Student ID: `230103215`; CPU: Intel Core i7-12650H; физические ядра: `10`; логические потоки: `16`; Windows 11; Python 3.12.10. Значения L1D (48 KiB для P-cores, 32 KiB для E-cores) и cache line 64 B — архитектурные ориентиры, а не отдельные измерения; L2=9728 KiB и L3=24576 KiB из твоего Windows PowerShell.

## Запуск в VS Code / PowerShell
Открой именно папку `minimal_parallel_lab_230103215` и последовательно выполни команды:

```powershell
python task0_cal.py --id 230103215
python task1_falsesharing.py --id 230103215 --physical 10
python task2_scaling.py --id 230103215 --physical 10
python task3a_roofline.py --id 230103215 --physical 10
python task3b_gemm.py --id 230103215 --physical 10
python task4_scheduling.py --id 230103215 --physical 10
python build_report.py --id 230103215 --physical 10 --cpu "Intel Core i7-12650H"
```

После выполнения появятся `phase0.json`, `phase1.json`, `phase2.json`, `phase3a.json`, `phase3b.json`, `phase4.json` и итоговый **`lab_report_230103215.md`**. Генератор оформит таблицы, рассчётные показатели, все реальные хеши, исходные JSON-логи и полный исходный код в одном файле.

**Не отправляй старый отчёт:** для Minimal Lab нужны 1 млн timer reads, 16 млн RMW, Nstrong 1.2 млн, Nweak0 200 тыс., 64 МБ × 2, 60 млн FLOPs на работника, GEMM 256² с BS {8,16,32,64,96,128}, scheduling 8 тыс. и C {1,8,64,512}.

`--quick` есть для проверки запуска (`python task1_falsesharing.py --id 230103215 --physical 10 --quick`), но результаты `--quick` нельзя использовать в итоговом отчёте: `build_report.py` их отклонит.

При возникновении ошибки сразу отправь полный traceback. На Windows процессы запускаются через `spawn`, и первые измерения могут иметь большие накладные расходы.

## Замечания по точности
- Реальные значения, временные замеры и хеши в архив **не вложены**: их необходимо получить на твоём ноутбуке. Генератор не придумывает результаты.
- В PDF указано выполнение offline без AI; следуй актуальным указаниям преподавателя насчёт допустимости помощи.
- Упрощённый benchmark Phase 3A измеряет Python throughput, а не native hardware FMA peak; поэтому Roofline — приближённый эмпирический ориентир.
- `harness.py` использует FNV-1a с точным форматированием `phase|id|Plog|metric1|metric2` до 4 знаков, и не должен изменяться между запуском и сдачей.
