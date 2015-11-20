#!/bin/bash

ps -ef | awk '/dstat.*\/tmp\/monStart.sh.log/ {system("kill " $2);}'

cat /tmp/monStart.sh.log | awk -F, '
    NR>7 && NF==15 {
        if (time_start == "") { time_start = $1 }; time_end = $1
        cpu_usage = 100 - $4;
        mem_total = $8 + $9 + $10 + $11
        if (mem_total == 0) { print NR, $0; next;}
        mem_used  = $8
        mem_usage = $8 * 100 / mem_total
        disk_read = $12
        disk_write= $13
        network_recv = $14
        network_send = $15
        
        num++;
        sum_cpu_usage+=cpu_usage; if (cpu_usage > max_cpu_usage) max_cpu_usage=cpu_usage; 
        sum_mem_used+=mem_used; if (mem_used > max_mem_used) max_mem_used=mem_used; 
        sum_mem_usage+=mem_usage; if (mem_usage > max_mem_usage) max_mem_usage=mem_usage; 
        sum_disk_read+=disk_read; if (disk_read > max_disk_read) max_disk_read=disk_read; 
        sum_disk_write+=disk_write; if (disk_write > max_disk_write) max_disk_write=disk_write; 
        sum_network_recv+=network_recv; if (network_recv > max_network_recv) max_network_recv=network_recv; 
        sum_network_send+=network_send; if (network_send > max_network_send) max_network_send=network_send; 
    }
    END {
        if (num==0) { print "Error: cannot find valid stat in /tmp/monStart.sh.log"; exit 1;}
        average_cpu_usage = sum_cpu_usage / num
        average_mem_used = sum_mem_used / num
        average_mem_usage = sum_mem_usage / num
        average_disk_read = sum_disk_read / num
        average_disk_write = sum_disk_write / num
        average_network_recv = sum_network_recv / num
        average_network_send = sum_network_send / num

        printf("Time: %s - %s\n", time_start, time_end)
        printf("Record: %d\n", num)
        print ""
        printf("CPU:  max: %.0f%  average: %.0f%\n", max_cpu_usage, average_cpu_usage)
        printf("MEM:  max: %.0f%(=%.0fM/%.0fM)  average: %.0f%(=%.0fM/%.0fM)\n", max_mem_usage, max_mem_used/1024/1024, mem_total/1024/1024, average_mem_usage, average_mem_used/1024/1024, mem_total/1024/1024)
        printf("DISK_READ :  max: %.0f/s  average: %.0f/s\n", max_disk_read, average_disk_read)
        printf("DISK_WRITE:  max: %.0f/s  average: %.0f/s\n", max_disk_write, average_disk_write)
        printf("NETWORK_RECV:  max: %.0f/s  average: %.0f/s\n", max_network_recv, average_network_recv)
        printf("NETWORK_SEND:  max: %.0f/s  average: %.0f/s\n", max_network_send, average_network_send)
    }
'
