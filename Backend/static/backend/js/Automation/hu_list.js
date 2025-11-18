let selectores = {
    userApp: '#selUserApp'
}

var vueHUList = new Vue({
    el: '#appHuList',
    delimiters: ['${','}$'],
    data:{
        automacao: null,
        hus: null,
        description: null,
        keys: null,
        name: null,
        cpf: null,
        telefone: null,
        signature: null,
        user_app: 0,
        users_app: null,
        condominio: {
            address: null,
            city: null
        },
        btnAddEnable: false,
        saving: false,
        sendingMqtt: false,
        endpoints: {
            save: null,
            sendToMqtt: null
        }
    },
    created: function(){
        this.loadDataFromTwig()
    },
    methods:{
        loadDataFromTwig: function(){
            this.endpoints.save = $("#endpoint-save").data('url')
            this.endpoints.sendToMqtt = $("#endpoint-send-mqtt").data('url')
            this.automacao = $('#automacao_id').val()
            this.hus = $('#hus').data('hus')
            this.users_app = $('#users_app').data('users_app')
            this.condominio.city = $('#city').data('city')
            this.condominio.address = $('#address').data('address')
        },
        openModalNewHU: function(){
            this.description = null
            this.keys = null
            $('#modal-new-hu').modal('show')
        },
        closeModalNewHU: function(){
            $('#modal-new-hu').modal('hide')
        },
        saveData: function(){

            let ctx = this

            if(!ctx.description){
                Swal.fire({
                  icon: "error",
                  title: "Oops...",
                  text: "O campo de descrição precisa ser de 5 dígitos!"
                });
                return false
            }

            if(!ctx.user_app){
                Swal.fire({
                  icon: "error",
                  title: "Oops...",
                  text: "É necessário selecionar um usuário que responde pela HU!"
                });
                return false
            }

            ctx.saving = true

            let data = {
                'automation_id':ctx.automacao,
                'description':ctx.description,
                'keys': ctx.keys,
                'user_app':ctx.user_app
            }

            $.get(ctx.endpoints.save, data, function(json){
                if(json.status == 200){
                    $.toast({
                        heading: 'Atenção',
                        text: json.description,
                        showHideTransition: 'slide',
                        icon: 'success'
                    })

                    ctx.hus.push({
                       id: json.id,
                       description: ctx.description,
                       keys: ctx.keys,
                       created_at: json.created_at
                    });


                    $('#modal-new-hu').modal('hide');
                    ctx.description = null
                    ctx.keys = null
                    ctx.user_app = 0;

                } else {
                    $.toast({
                        heading: 'Atenção',
                        text: json.description,
                        showHideTransition: 'slide',
                        icon: 'error'
                    });
                }
            }, 'json');

            setTimeout(function(){
                ctx.saving = false
            },5e3);

        },
        sendToAutomation: function(){
            let ctx = this

            if(!ctx.hus || ctx.hus.length == 0){

                $.toast({
                    heading: 'Atenção',
                    text: 'Não há o que enviar!',
                    showHideTransition: 'slide',
                    icon: 'warning'
                });

                return false;
            }

            let data = {
                'automation': ctx.automacao,
                'hus': ctx.hus,
                'city': ctx.condominio.city,
                'address': ctx.condominio.address
            }

            ctx.saving = true

            $.post(ctx.endpoints.sendToMqtt, JSON.stringify(data), function(json){

                ctx.sendingMqtt = false

                if(json.status == 200){
                    $.toast({
                        heading: 'Atenção',
                        text: json.description,
                        showHideTransition: 'slide',
                        icon: 'success'
                    })

                } else {
                    $.toast({
                        heading: 'Atenção',
                        text: json.description,
                        showHideTransition: 'slide',
                        icon: 'error'
                    });
                }
            }, 'json');

            setTimeout(function(){
                ctx.saving = false
            },60e3);
        },
        deleteConfirm: function(url, id){

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
                let url_del = url.replaceAll('__pk__', id)
                fetch(url_del).
                then(response => {
                    if(response.ok){
                        return response.json();
                    }else{
                        console.log('Erro na ação GET:', response.status);
                        toastr.error(response.status);
                    }
                })
                .then(data => {
                    Swal.fire(
                      'Excluído',
                      'O registro foi excluído com sucesso!',
                      'success'
                    )
                    window.location.reload()
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
        },
    },
    watch: {
        description: function(newValue, oldValue){
            if(newValue){
                if(newValue.length == 5){
                    this.btnAddEnable = true
                }else{
                    this.btnAddEnable = false
                }
            }else{
                this.btnAddEnable = false
            }
        }
    }
});

$(function(){
    $(document).on('change', selectores.userApp, function(){
        vueHUList.user_app = $(`${selectores.userApp} option:selected`).val();
    });
});