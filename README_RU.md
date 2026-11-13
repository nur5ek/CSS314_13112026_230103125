
## Порядок запуска в Windows PowerShell

1. Установить Python 3 и распаковать ZIP в папку `parallel_lab`.
2. Открыть папку в VS Code, затем Terminal → New Terminal.
3. Узнать **свои** физические ядра (NumberOfCores) и модель CPU:

```powershell
Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,L2CacheSize,L3CacheSize
```

4. В командах заменить `YOUR_ID` на свой Student ID, `CORES` на физическое число ядер, а `CPU_NAME`, `L1`, `L2`, `L3`, `LINE` — на измеренные характеристики.

```powershell
python task0_cal.py --id YOUR_ID
python task1_falsesharing.py --id YOUR_ID --physical CORES
python task2_scaling.py --id YOUR_ID --physical CORES
python task3a_roofline.py --id YOUR_ID --physical CORES
python task3b_gemm.py --id YOUR_ID --physical CORES
python task4_scheduling.py --id YOUR_ID --physical CORES
python build_report.py --id YOUR_ID --physical CORES --cpu "CPU_NAME" --l1 "L1" --l2 "L2" --l3 "L3" --cache-line "LINE"
```

Результаты сохраняются в `phase*.json`; отчет формируется как `lab_report_YOUR_ID.md`.

## Быстрая проверка кода

Каждая программа `task1` ... `task4` принимает `--quick`, что резко уменьшает нагрузку. **Быстрые результаты не подходят для сдачи**, так как изменяют объемы задач по сравнению с PDF.

## Ограничения и важные проверки

- Запускайте реальные измерения только на своем ноутбуке; в подготовленном ZIP нет выдуманных значений или хешей.
- Не редактируйте цифры и HASH вручную — значения связаны с измерениями.
- Описанный в PDF `harness.py` содержит опечатки верстки; здесь применена синтаксически корректная версия.
- В задаче Phase 3A формула пропускной способности в PDF требует внимательности к единицам измерения; скрипт использует секунды и перевод в GB/s.
- В Phase 1 кратковременное межпроцессное создание процессов включено в замеры; это может маскировать аппаратный эффект false sharing.
- Phase 3B не сравнивает верификацию для каждого размера тайла; при подготовке собственного отчета лучше дополнительно проверить каждый вариант.
- В `task4_scheduling.py` формула нагрузки реализована как `1 + (i // 60)**2`; если преподаватель трактует формулу как `floor((i/60)**2)`, замените на `1 + (i*i)//3600` (они немного отличаются).
- По результатам опытов допишите аналитические объяснения собственными словами.
