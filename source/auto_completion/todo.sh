_todo() 
{
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="add done task edit rm ctx contexts history purge"
    if [ ${prev} = 'todo' ]; then
        COMPREPLY=( $(compgen -W "${commands}" ${cur}) )
        return 0
    fi

    if [ ${prev} = '-c' -o ${prev} = 'ctx' ]; then
        data_dir="$HOME/.toduh"
        if [ -d '.toduh' ]; then
            data_dir='.toduh'
        fi
        data_file="$data_dir/contexts"
        if [ -f $data_file ]; then
            contexts=`cat $data_file`
            COMPREPLY=( $(compgen -W "${contexts}" ${cur}) )
            return 0
        fi
    fi       
}
complete -F _todo todo
