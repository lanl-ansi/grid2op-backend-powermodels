# For testing basic python-julia interactions

value = "nothing"

function reset()
    global value = "nothing"
end

function set_foo()
    global value = "foo"
end

function set_bar()
    global value = "bar"
end

function set_value(v::String)
    global value = v
end

function get_value()
    return value
end



function interactive_mode()
    println(stderr, "staring interactive mode...")

    result = "None"
    while true
        println("waiting for input line...")
        line = readline()
        line = strip(line)

        if startswith(line, "shutdown")
            println(stderr, "stopping interactive mode")
            println("")
            println("complete")
            break

        elseif startswith(line, "set_value")
            v = string(strip(split(line, ",")[2]))
            set_value(v)
            println("")
            println("complete")

        elseif startswith(line, "set_foo")
            set_foo()
            println("")
            println("complete")

        elseif startswith(line, "set_bar")
            set_bar()
            println("")
            println("complete")

        elseif startswith(line, "get_value")
            value = get_value()
            println(value)
            println("complete")

        elseif startswith(line, "reset")
            reset()
            println("")
            println("complete")

        else
            println(stderr, "command not recognized, $(line)")
            println("")
            println("error")
        end
    end
end

