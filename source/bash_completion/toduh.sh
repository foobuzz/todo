_todo() 
{
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="add done task edit rm ctx mv rmctx contexts history purge --location --help"

    data_dir="$HOME/.toduh"
    if [ -d '.toduh' ]; then
        data_dir='.toduh'
    fi
    data_file="$data_dir/contexts"
    if [ -f $data_file ]; then
        contexts=`cat $data_file`
    fi

    if [ ${prev} = 'todo' ]; then
        COMPREPLY=( $(compgen -W "${commands} ${contexts}" -- ${cur}) )
        return 0
    fi

    if [[ ${prev} = '-c' ||
          ${prev} = '--context' ||
          ${prev} = 'ctx' ||
          ${prev} = 'rmctx' ||
          ${prev} = 'mv' ||
          ${COMP_WORDS[COMP_CWORD-2]} = 'mv' ]]; then
        COMPREPLY=( $(compgen -W "${contexts}" ${cur}) )
        return 0
    fi

    if [ ${prev} = '-v' -o ${prev} = '--visibility' ]; then
        visibilities="hidden normal"
        COMPREPLY=( $(compgen -W "${visibilities}" ${cur}) )
        return 0
    fi
}
complete -F _todo todo
