package require http
package require tls
package require json

::http::register https 443 ::tls::socket

proc jsonGet {_RESULT url} {
    upvar 1 $_RESULT RESULT

    set tok [::http::geturl $url]
    if {[::http::status $tok] != "ok"} {
        error "Failed to \[jsonPost $url $json\] with returned tok:\n{[array get $tok]}"
    }
    if {$_RESULT != ""} {
        set RESULT [::json::json2dict [::http::data $tok]]
    }
    ::http::cleanup $tok
}

proc jsonPost {_RESULT url json} {
    upvar 1 $_RESULT RESULT

    set tok [::http::geturl $url -type application/json -query "{$json}"]
    if {[::http::status $tok] != "ok"} {
        error "Failed to \[jsonPost $url $json\] with returned tok:\n{[array get $tok]}"
    }
    if {$_RESULT != ""} {
        set RESULT [::json::json2dict [::http::data $tok]]
    }
    ::http::cleanup $tok
}

proc jsonFormat {RESULT {INDENT ""}} {
    set ret ""
    foreach {key value} $RESULT {
        switch -exact -- $key {
            response - job {
                append ret "$INDENT$key:\t{\n"
                if {[llength [lindex $value 0]] == 1} {
                    append ret [jsonFormat $value "$INDENT\t"]
                } else {
                    foreach val [lsort $value] {
                        append ret [jsonFormat $val "$INDENT\t"]
                    }
                }
                append ret "$INDENT}\n"
            }
            options {
                append ret "$INDENT$key:\t{\n"
                foreach val $value {
                    append ret "$INDENT\t{$val}\n"
                }
                append ret "$INDENT}\n"
            }
            default {
                append ret "$INDENT$key:\t$value\n"
            }
        }
    }
    return $ret
}
