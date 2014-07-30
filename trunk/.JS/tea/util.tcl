proc nowtime {{seconds -1}} {
    if {$seconds < 0} { set seconds [clock seconds] }
    return [clock format $seconds -format %T]
}
proc nowtimeAdd {} {
    set now [clock seconds]
    if {![info exists ::nowtimeAdd_last]} {
        set ::nowtimeAdd_last $now
        set add 0
    } else {
        set add [expr {$now-$::nowtimeAdd_last}]
    }
    set ::nowtimeAdd_last $now
    return "+[clock format $add -format %T -gmt 1] [clock format $now -format %T]"
}
