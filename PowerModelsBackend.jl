
import PowerModels
import Ipopt

PowerModels.silence()
# TODO figure out how to direct Memento to stderr

#nlp_solver = optimizer_with_attributes(Ipopt.Optimizer, "tol"=>1e-6, "print_level"=>0)
nlp_solver = PowerModels.optimizer_with_attributes(Ipopt.Optimizer, "tol"=>1e-6)

data = Dict{String,Any}()


function reset()
    global nlp_solver = PowerModels.optimizer_with_attributes(Ipopt.Optimizer, "tol"=>1e-6)
    global data = Dict{String,Any}()
end

function load_grid(file::String)
    global data = PowerModels.parse_file(file)
end

function run_ac_pf()
    result = PowerModels.run_ac_pf(data, nlp_solver)
    if result["termination_status"] == PowerModels.LOCALLY_SOLVED
        PowerModels.update_data!(data, result["solution"])
    else
        println(stderr, "error in run_ac_pf solver, termination status is $(result["termination_status"])")
    end

    return result["termination_status"] == PowerModels.LOCALLY_SOLVED
end

function run_dc_pf()
    result = PowerModels.run_dc_pf(data, nlp_solver)
    if result["termination_status"] == PowerModels.LOCALLY_SOLVED
        PowerModels.update_data!(data, result["solution"])
    else
        println(stderr, "error in run_dc_pf solver, termination status is $(result["termination_status"])")
    end

    return result["termination_status"] == PowerModels.LOCALLY_SOLVED
end

function data_summary()
    result = PowerModels.summary(stderr, data)
end



function interactive_mode()
    println(stderr, "staring interactive mode...")

    result = "None"
    while true
        println("waiting for input line...")
        line = readline()

        if startswith(line, "shutdown")
            println(stderr, "stopping interactive mode")
            println("")
            println("complete")
            break

        elseif startswith(line, "load_grid")
            file = string(strip(split(line, ",")[2]))
            load_grid(file)
            #redirect_stdout(() -> load_grid(file), stderr)
            println("")
            println("complete")

        elseif startswith(line, "data_summary")
            data_summary()
            println("")
            println("complete")

        elseif startswith(line, "run_ac_pf")
            #run_ac_pf()
            converged = redirect_stdout(run_ac_pf, stderr)
            println(converged)
            println("complete")

        elseif startswith(line, "run_dc_pf")
            converged = redirect_stdout(run_dc_pf, stderr)
            println(converged)
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

