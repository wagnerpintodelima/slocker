var vueEdit = new Vue({
    el: '#appEditPosVendas',
    delimiters: ['${','}$'],
    data:{
        path_star: null,
        path_star_line: null,
        hover1: false,
        hover2: false,
        hover3: false,
        hover4: false,
        hover5: false,
        descricao_atendimento: null,
        satisfacao: -1,
        showOS: false
    },
    mounted: function(){
        this.loadDataFromTwig();
    },
    methods:{
        loadDataFromTwig: function(){
            this.path_star = $('#icon_star').val()
            this.path_star_line = $('#icon_star_line').val()
        },

        selSatisfacao: function(elemento){
            let ctx = this

            ctx.satisfacao = elemento            

        }
    }
});


