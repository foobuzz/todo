_todo() 
{
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="add done task edit rm ctx contexts history purge --location --help"

    data_dir="$HOME/.toduh"
    if [ -d '.toduh' ]; then
        data_dir='.toduh'
    fi
    data_file="$data_dir/contexts"
    if [ -f $data_file ]; then
        contexts=`cat $data_file`
    fi

    if [ ${prev} = 'todo' ]; then
        COMPREPLY=( $(compgen -W "${commands} ${contexts} LAST" -- ${cur}) )
        return 0
    fi

    if [ ${prev} = '-c' -o ${prev} = '--context' -o ${prev} = 'ctx' ]; then
        COMPREPLY=( $(compgen -W "${contexts} LAST" ${cur}) )
        return 0
    fi

    if [ ${prev} = '-v' -o ${prev} = '--visibility' ]; then
        visibilities="hidden discreet wide"
        COMPREPLY=( $(compgen -W "${visibilities}" ${cur}) )
        return 0
    fi
}
complete -F _todo todo
