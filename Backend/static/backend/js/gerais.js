var vueIndex = new Vue({
    el: '#header',
    delimiters: ['${','}$'],
    data:{
        endpoints: {
            callGetData: null,
            callSave: null
        },
        cliente: -1,
        tecnico: -1,
        assunto: -1,
        dataehora: null,
        problema: null,
        clientes: [],
        tecnicos: [],
        assuntos: []
    },
    mounted: function(){
        this.loadDataFromTwig()        

        const formatada = new Date().toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false
        }).replace(",", ""); // Remove a vírgula entre data e hora

        this.dataehora = formatada

        
        const vm = this;

        $('#select-cliente').select2({ width: '100%' }).on('change', function () {
            vm.cliente = $(this).val();
        });

        $('#select-assunto').select2({ width: '100%' }).on('change', function () {
            vm.assunto = $(this).val();
        });

        $('#select-tecnico').select2({ width: '100%' }).on('change', function () {
            vm.tecnico = $(this).val();
        });

    },
    methods:{
        loadDataFromTwig: function(){
            this.endpoints.callGetData = $('#CallGetData').val()
            this.endpoints.callSave = $('#CallSave').val()
        },

        openModalCall: function(){
            $.get(this.endpoints.callGetData, (dados) => {
                this.clientes = dados.clientes
                this.tecnicos = dados.tecnicos
                this.assuntos = dados.ASSUNTO_CALL_CHOICES
                $('#modalCall').show()
            })
        },

        saveCall: function(){
            debugger
            if(this.cliente == -1 || this.assunto == -1 || this.tecnico == -1 || this.problema == '' || !this.dataehora){
                $.toast({
                    heading: 'Atenção',
                    text: 'Você precisa preencher todos os campos!',
                    showHideTransition: 'slide',
                    icon: 'error',
                    hideAfter: 2000,
                    position: 'top-right', // bottom-left or bottom-right or bottom-center or top-left or top-right or top-center or mid-center or an object representing the left, right, top, bottom values
                });
                return
            }

            let package = {
                cliente: this.cliente,
                assunto: this.assunto,
                tecnico: this.tecnico,
                dataehora: this.dataehora,
                problema: this.problema
            }

            $.post(this.endpoints.callSave, JSON.stringify(package), (response) =>{
                if(response.status == 200){
                    $.toast({
                        heading: 'Atenção',
                        text: response.description,
                        showHideTransition: 'slide',
                        icon: 'success',
                        hideAfter: 2000,
                        position: 'top-right', // bottom-left or bottom-right or bottom-center or top-left or top-right or top-center or mid-center or an object representing the left, right, top, bottom values
                    });
                }else{
                    $.toast({
                        heading: 'Atenção',
                        text: response.description,
                        showHideTransition: 'slide',
                        icon: 'error',
                        hideAfter: 60000,
                        position: 'top-right', // bottom-left or bottom-right or bottom-center or top-left or top-right or top-center or mid-center or an object representing the left, right, top, bottom values
                    });
                }

                this.closeModalCall()
            })

            

        },

        closeModalCall: function(){
            $('#modalCall').hide()
        }
    },
    watch: {
        cliente(newVal) {
            $('#select-cliente').val(newVal).trigger('change');
        },
        assunto(newVal) {
        $('#select-assunto').val(newVal).trigger('change');
        },
        tecnico(newVal) {
        $('#select-tecnico').val(newVal).trigger('change');
        }
    }
});



$(function(){
    
    $('.date').mask('00/00/0000');
    $('.time').mask('00:00:00');
    $('.date_time').mask('00/00/0000 00:00');
    $('.cep').mask('00.000-000', {clearIfNotMatch: true});
    $('.phone').mask('(00) 0 0000-0000', {clearIfNotMatch: true});
    $('.cpf').mask('000.000.000-00', {reverse: true, clearIfNotMatch: true});
    $('.cnpj').mask('00.000.000/0000-00', {reverse: true, clearIfNotMatch: true});
    $('.money').mask('000.000.000.000.000,00', {reverse: true});
    $('.ip_address').mask('0ZZ.0ZZ.0ZZ.0ZZ', {
        translation: {
            'Z': {
            pattern: /[0-9]/, optional: true
        }
        }
    });
    $('.ip_address').mask('099.099.099.099');
    $('.percent').mask('##0,00%', {reverse: true});
    $('.clear-if-not-match').mask("00/00/0000", {clearIfNotMatch: true});
    $('.placeholder').mask("00/00/0000", {placeholder: "__/__/____"});        
    

});