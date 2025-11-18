let selectores = {
    solenoide_address: '#solenoide_address'
}

var vueSLOTList = new Vue({
    el: '#appSlotList',
    delimiters: ['${','}$'],
    data:{
        slots: null,
        hus: null,
        automacao: null,
        id_in_array_slots: null,
        name: null,
        solenoide_address: null,
        model: null,
        status: null,
        descriptionEdit: null,
        passwordEdit: null,
        statusEdit: null,
        endpoints: {
            save: null,
            sendToMqtt: null,
            sendToMqttEdit: null
        },
        btnSaveEnable: false,
        btnMqttEnable: true,
        saving: false,
        btnSaveEnableEdit: false,
        btnMqttEnableEdit: true,
        savingEdit: false,
        descricaoStatus: ['Fechado','Aguardando abertura porta','Aguardando fechamento porta','Autorizado para receber','Abertura não autorizada','Cancelado'],
        descricaoModel: ['Pequeno','Médio','Grande'],
        slotSelected: null
    },
    created: function(){
        this.loadDataFromTwig()
    },
    methods:{
        loadDataFromTwig: function(){
            this.endpoints.save = $("#endpoint-save").data('url')
            this.endpoints.sendToMqtt = $("#endpoint-send-mqtt").data('url')
            this.endpoints.sendToMqttEdit = $("#endpoint-send-mqtt-edit").data('url')
            this.slots = $("#slots").data('slots')
            this.hus = $("#hus").data('hus')
            this.automacao = $('#automacao_id').val()
        },
        openModalNewSlot: function(){
            $('#modal-new-slot').modal('show')
        },
        closeModalNewSlot: function(){
            $('#modal-new-slot').modal('hide')
        },
        saveData: function(){

            let ctx = this
            ctx.saving = true

            if(ctx.id_in_array_slots == null || ctx.name == null || ctx.solenoide_address == null || ctx.model == null || ctx.status == null){
                $.toast({
                    heading: 'Atenção',
                    text: 'Formulário inválido!',
                    showHideTransition: 'slide',
                    icon: 'warning'
                });

                return false
            }

            if((ctx.password != null && ctx.description == null)||(ctx.password == "" && ctx.description != null)){
                $.toast({
                    heading: 'Atenção',
                    text: 'Se há senha, deve haver um apartamento!',
                    showHideTransition: 'slide',
                    icon: 'warning'
                });

                return false
            }

            let data = {
                'automation_id': ctx.automacao,
                'id_in_array_slots': ctx.id_in_array_slots,
                'name': ctx.name,
                'solenoide_address': ctx.solenoide_address,
                'model': ctx.model,
                'status': ctx.status,
                'description': ctx.description,
                'password': ctx.password
            }

            $.toast({
                heading: 'Aguarde',
                text: 'Enviando dados...',
                showHideTransition: 'slide',
                icon: 'warning'
            })

            $.get(ctx.endpoints.save, JSON.stringify(data), function(json){

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

            ctx.saving = false

            ctx.closeModalNewSlot()

            // form data
            ctx.id_in_array_slots = null
            ctx.name = null
            ctx.solenoide_address = null
            ctx.model = null
            ctx.status = null
            ctx.password = null
            ctx.description = null

            setTimeout(function(){
                window.location.reload();
            }, 2e3);
        },
        showButtonSave: function(){
            let ctx = this
            if(ctx.id_in_array_slots != null && ctx.name != null && ctx.solenoide_address != null && ctx.model != null && ctx.status != null){
                if((ctx.password != null && ctx.description == null)||(ctx.password == null && ctx.description != null)){
                    ctx.btnSaveEnable = false
                }else{
                    ctx.btnSaveEnable = true
                }
            }else{
                ctx.btnSaveEnable = false
            }
        },
        showButtonSaveEdit: function(){
            let ctx = this
            if(ctx.statusEdit != null && ctx.passwordEdit != null && ctx.descriptionEdit != null){
                if(ctx.passwordEdit.length != 5){
                    ctx.btnSaveEnableEdit = false
                }else{
                    if(ctx.slots.find(slot => slot.fields.passwordEdit === ctx.passwordEdit)){
                        $.toast({
                            heading: 'Atenção',
                            text: 'Essa senha já está em uso!',
                            showHideTransition: 'slide',
                            icon: 'error'
                        });
                        ctx.btnSaveEnableEdit = false
                        ctx.passwordEdit = null
                    }else{
                        ctx.btnSaveEnableEdit = true
                    }
                }
            }else{
                ctx.btnSaveEnableEdit = false
            }
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
        loadMQTTConfirm: function(){

            let ctx = this
            ctx.btnMqttEnable = false

            let data = {
                'automation': ctx.automacao
            }

            Swal.fire({
              title: 'Tem certeza?',
              text: "Você vai re/configurar todos os SLOTS do uC!!!",
              icon: 'warning',
              showCancelButton: true,
              confirmButtonColor: '#3085d6',
              cancelButtonColor: '#d33',
              confirmButtonText: 'Sim, manda brasa!',
              cancelButtonText: 'Deixe quieto!',
            }).then((result) => {
              if (result.isConfirmed) {

                $.get(ctx.endpoints.sendToMqtt, JSON.stringify(data), function(json){
                    if(json.status == 200){
                        Swal.fire(
                          'Atenção',
                          json.description,
                          'success'
                        )
                        window.location.reload()
                    } else {
                        Swal.fire(
                          'Atenção',
                          json.description,
                          'error'
                        )
                        ctx.btnMqttEnable = true
                    }
                }, 'json');

                setTimeout(function(){
                    ctx.btnMqttEnable = true
                },5e3);
              }else{
                Swal.fire(
                  'Cancelado',
                  'Ok, não enviamos nenhuma carga para o microcontrolador!',
                  'error'
                )
                ctx.btnMqttEnable = true
              }
            });
        },
        openModalEdit: function(slot){
            this.slotSelected = slot
            $('#modal-edit-slot').modal('show')
        },
        closeModalEdit: function(){
            this.slotSelected = null
            $('#modal-edit-slot').modal('hide')
        },
        saveDataEdit: function(){

            let ctx = this
            ctx.savingEdit = true

            if(ctx.statusEdit == null || ctx.passwordEdit == null || ctx.descriptionEdit == null){
                $.toast({
                    heading: 'Atenção',
                    text: 'É necessário informar os três campos!',
                    showHideTransition: 'slide',
                    icon: 'warning'
                });

                return false
            }

            let data = {
                'slot_id': ctx.slotSelected.pk,
                'empty': false, // Setando novos dados
                'status': ctx.statusEdit,
                'description': ctx.descriptionEdit,
                'password': ctx.passwordEdit
            }

            Swal.fire({
              title: 'Tem certeza?',
              text: "Você vai alterar dados no SLOT em produção, é isso mesmo???",
              icon: 'warning',
              showCancelButton: true,
              confirmButtonColor: '#3085d6',
              cancelButtonColor: '#d33',
              confirmButtonText: 'Sim, manda brasa!',
              cancelButtonText: 'Deixe quieto!',
            }).then((result) => {
              if (result.isConfirmed) {

                $.get(ctx.endpoints.sendToMqttEdit, JSON.stringify(data), function(json){

                    if(json.status == 200){
                        Swal.fire(
                          'Atenção',
                          json.description,
                          'success'
                        )
                        window.location.reload()
                    } else {
                        Swal.fire(
                          'Atenção',
                          json.description,
                          'error'
                        )
                    }
                }, 'json');

                setTimeout(function(){
                    ctx.btnMqttEnableEdit = true
                    window.location.reload();
                },2e3);

                ctx.savingEdit = false
                ctx.closeModalEdit()

              }else{
                Swal.fire(
                  'Cancelado',
                  'Ok, não enviamos nenhuma carga para o microcontrolador!',
                  'error'
                )
                ctx.btnMqttEnableEdit = true
                ctx.savingEdit = false
              }
            });
        },
        saveDataEditEmpty: function(){

            let ctx = this
            ctx.savingEdit = true

            let data = {
                'slot_id': ctx.slotSelected.pk,
                'empty': true // Limpando dados desse slot
            }

            Swal.fire({
              title: 'Tem certeza?',
              text: "Você vai alterar dados no SLOT em produção, é isso mesmo???",
              icon: 'warning',
              showCancelButton: true,
              confirmButtonColor: '#3085d6',
              cancelButtonColor: '#d33',
              confirmButtonText: 'Sim, manda brasa!',
              cancelButtonText: 'Deixe quieto!',
            }).then((result) => {
              if (result.isConfirmed) {

                $.get(ctx.endpoints.sendToMqttEdit, JSON.stringify(data), function(json){

                    if(json.status == 200){
                        Swal.fire(
                          'Atenção',
                          json.description,
                          'success'
                        )
                        window.location.reload()
                    } else {
                        Swal.fire(
                          'Atenção',
                          json.description,
                          'error'
                        )
                    }
                }, 'json');

                setTimeout(function(){
                    ctx.btnMqttEnableEdit = true
                    window.location.reload();
                },2e3);

                ctx.savingEdit = false
                ctx.closeModalEdit()

              }else{
                Swal.fire(
                  'Cancelado',
                  'Ok, não enviamos nenhuma carga para o microcontrolador!',
                  'error'
                )
                ctx.btnMqttEnableEdit = true
                ctx.savingEdit = false
              }
            });
        },
        onlyNumbers(event) {
        // Filtra os caracteres não numéricos
        this.password = event.target.value.replace(/\D/g, '');
      }
    },
    watch: {
        id_in_array_slots: function(newValue, oldValue){
            if(newValue == 'null')  this.id_in_array_slots = null
            this.showButtonSave()
        },
        name: function(newValue, oldValue){
            if(newValue == 'null')  this.name = null
            this.showButtonSave()
        },
        solenoide_address: function(newValue, oldValue){
            if(newValue == 'null')  this.solenoide_address = null
            this.showButtonSave()
        },
        model: function(newValue, oldValue){
            if(newValue == 'null')  this.model = null
            this.showButtonSave()
        },
        status: function(newValue, oldValue){
            if(newValue == 'null')  this.status = null
            this.showButtonSave()
        },
        statusEdit: function(newValue, oldValue){
            if(newValue == 'null')  this.statusEdit = null
            this.showButtonSaveEdit()
        },
        passwordEdit: function(newValue, oldValue){
            if(newValue == "") this.passwordEdit = null
            this.showButtonSaveEdit()
        },
        descriptionEdit: function(newValue, oldValue){
            if(newValue == 'null')  this.descriptionEdit = null
            this.showButtonSaveEdit()
        }
    }
});

$(function(){
    $(document).on('change', selectores.solenoide_address, function(){
        vueSLOTList.solenoide_address = $(`${selectores.solenoide_address} option:selected`).val();
    });
});