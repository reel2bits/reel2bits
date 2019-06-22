<template>
    <div>
        <h4>register</h4>
        <form @submit.prevent="register">
            <label for="name">username</label>
            <div><input id="username" type="text" v-model="username" required autofocus></div>

            <label for="email">email</label>
            <div><input id="email" type="email" v-model="email" required></div>

            <label for="password">password</label>
            <div><input id="password" type="password" v-model="password" required></div>

            <label for="password_confirmation">password confirmation</label>
            <div><input id="password_confirmation" type="password" v-model="password_confirmation" required></div>

            <div><button type="submit">register</button></div>
        </form>
    </div>
</template>

<script>
export default {
    data () {
        return {
            username: '',
            email: '',
            password: '',
            password_confirmation: '',
            is_admin: null
        }
    },
    methods: {
        register: function () {
            let data = {
                username: this.username,
                email: this.email,
                password: this.password,
                is_admin: this.is_admin
            }
            this.$store.dispatch('register', data)
            .then(() => this.$router.push('/'))
            .catch(err => console.log(err))
        }
    }
}
</script>
