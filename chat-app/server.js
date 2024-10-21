//sunucu kurma
const express = require('express')
const socket = require('socket.io')

const app = express()
const server = app.listen(3000)

app.use(express.static('public'))

//server tanımlıcaz soket çağırıp 
const io = socket(server)

//connection kontrolu
io.on('^connection', (socket)=>{
    console.log(socket.id) //her kullanıcı unique id
})
