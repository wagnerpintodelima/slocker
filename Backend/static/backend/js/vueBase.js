var vueBase = new Vue({
    el: '#appBase',
    delimiters: ['${','}$'],
    data:{

    },
    mounted: function(){
        this.loadDataFromTwig();
    },
    methods:{
        loadDataFromTwig: function(){

        },
        deleteConfirm: function(url){

            if(!url)    return false

            Swal.fire({
              title: 'Tem certeza?',
              text: "Você não pode desfazer isso!",
              icon: 'warning',
              showCancelButton: true,
              confirmButtonColor: '#3085d6',
              cancelButtonColor: '#d33',
              confirmButtonText: 'Sim, exclua!',
              cancelButtonText: 'Cancelar',
            }).then((result) => {
              if (result.isConfirmed) {
                fetch(url).
                then(response => {
                    if(response.ok){
                        return response.json();
                    }else{
                        console.log('Erro na ação GET:', response.status);
                        toastr.error(response.status);
                    }
                })
                .then(data => {
                    console.log(data);
                    Swal.fire(
                      'Excluído',
                      'O registro foi excluído com sucesso!',
                      'success'
                    )
                })
                .catch(error => {
                    console.log(`ocorreu o erro ${error}`);
                });
              }else{
                Swal.fire(
                  'Cancelado',
                  'Ok, seu registro NÃO foi excluído',
                  'error'
                )
              }
            });
        }
    }
});