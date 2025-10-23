<template>
  <!-- 高拍仪视频预览区 -->
  <div id="view">
    <img id="view1" src="http://127.0.0.1:38088/video=stream&camidx=0" alt="主摄像头">
    <img id="view2" src="http://127.0.0.1:38088/video=stream&camidx=1" alt="副摄像头">
  </div>
  <!-- 缩略图 -->
  <div id="suoluetu"></div>
  <!-- 功能按钮 -->
  <div id="myactive">
    主摄像头视频模式：<select id="view1_mode" v-model="view1_mode_selected" @change="view1_mode_change(view1_mode_selected)"><option v-for="item in view1_mode_list" :key="item.key" :value="item.key">{{item.value}}</option></select>
    主摄像头分辨率：<select id="view1_resolution_power" v-model="view1_resolution_selected"><option v-for="(item, index) in view1_resolution_list" :key="index" :value="item">{{item}}</option></select>
    副摄像头视频模式：<select id="view2_mode" v-model="view2_mode_selected" @change="view2_mode_change(view2_mode_selected)"><option v-for="item in view2_mode_list" :key="item.key" :value="item.key">{{item.value}}</option></select>
    副摄像头分辨率：<select id="view2_resolution_power" v-model="view2_resolution_selected"><option v-for="(item, index) in view2_resolution_list" :key="index" :value="item">{{item}}</option></select>
    <br>
    <button @click="open_view1">打开主摄像头视频</button>
    <button @click="close_view1">关闭主摄像头视频</button>
    <button @click="open_view2">打开副摄像头视频</button>
    <button @click="close_view2">关闭副摄像头视频</button>
    <button @click="rotate(90)">左转</button>
    <button @click="rotate(270)">右转</button>
    <br>
    <button @click="view1_scan">主摄像头拍照</button>
    <button @click="view2_scan">副摄像头拍照</button>
    <button @click="flat_scan">展平拍照</button>
    <button @click="open_auto_scan">开启自动拍照</button>
    <button @click="close_auto_scan">关闭自动拍照</button>
    <br>
    <button @click="getcode">条码识别</button>
    <button @click="getbiokey">获取指纹</button>
    <button @click="getidcard">读取身份证</button>
    <button @click="sign_a">弹出签字窗口：GW500A & GW1000A</button>
    <button @click="sign_a_get">获取签名图片：GW500A & GW1000A</button>
    <br>
    <button @click="start_video">开始录制视频</button>
    <button @click="end_video">结束录制视频</button>
    <button @click="get_state_video">获取视频录制状态</button>
    <button @click="get_audio">获取音频设备列表</button>
    <br>
    <button @click="open_a3a4">开启A3A4幅面自动切换：S1840</button>
    <button @click="close_a3a4">关闭A3A4幅面自动切换：S1840</button>
    <br>
    <button @click="add_pdf">拍照并加入PDF队列</button>
    <button @click="save_pdf">生成PDF文件</button>
    <br>
    <button @click="is_living_person">活体检测</button>
    <button @click="person_and_IDCard">人证比对</button>
    <br>
    <button @click="ocr">OCR</button>
    <br>
    <button @click="getequipmenttype">获取设备型号</button>
    <button @click="getsonixserialnumber">获取设备序列号</button>
    <button @click="get_state">获取设备状态</button>
    <button @click="is_con">判断设备是否连接</button>
    <br>
    <button @click="open_serialport">打开串口</button>
    <button @click="close_serialport">关闭串口</button>
    <!-- <button>评价窗口弹出</button> -->
    <button @click="sign_r">签字窗口弹出：GW500R & GW1000R</button>
    <button @click="sign_r_get">获取签名图片: GW500R & GW1000R</button>
  </div>
  <!-- 操作日志 -->
  <div id="mylog">首次打开页面，没有显示出分辨率信息？不要急，刷新下页面就可以了<br>我是操做日志，如果我出现问题，请看控制台信息......</div>
</template>

<script>
import {defineComponent, ref} from 'vue'
import axios from 'axios'
export default defineComponent({
  name: 'App',
  created(){
    // 加载主摄像头视频模式
    let view1_mode_data1 = { "camidx": "0", "mode": "0" };
    let view1_mode_data2 = { "camidx": "0", "mode": "1" };
    axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(view1_mode_data2)).then((res)=>{
      if(res.data.data.split("|").length > 1){
        let data = new Object()
        data.key = '1'
        data.value = 'MJPG'
        this.view1_mode_list.push(data)
      }
    })
    axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(view1_mode_data1)).then((res)=>{
      if(res.data.data.split("|").length > 1){
        let data = new Object()
        data.key = '0'
        data.value = 'YUY2'
        this.view1_mode_list.push(data)
      }
    })

    // 加载主摄像头分辨率
    let view1_resolution_power_data = {"camidx": "0", "mode": this.view1_mode_selected}
    axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(view1_resolution_power_data)).then((res)=>{
      let resolution_list = res.data.data.split("|");
      this.view1_resolution_selected = resolution_list[0]
      for(var i=0; i<resolution_list.length; i++){
        this.view1_resolution_list.push(resolution_list[i])
      }
    })

    // 加载副摄像头视频模式
    let view2_mode_data1 = { "camidx": "1", "mode": "0" };
    let view2_mode_data2 = { "camidx": "1", "mode": "1" };
    axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(view2_mode_data2)).then((res)=>{
      if(res.data.data.split("|").length > 1){
        let data = new Object()
        data.key = '1'
        data.value = 'MJPG'
        this.view2_mode_list.push(data)
      }
    })
    axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(view2_mode_data1)).then((res)=>{
      if(res.data.data.split("|").length > 1){
        let data = new Object()
        data.key = '0'
        data.value = 'YUY2'
        this.view2_mode_list.push(data)
      }
    })

    // 加载副摄像头分辨率
    let view2_resolution_power_data = {"camidx": "1", "mode": this.view2_mode_selected}
    axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(view2_resolution_power_data)).then((res)=>{
      let resolution_list = res.data.data.split("|");
      this.view2_resolution_selected = resolution_list[0]
      for(var i=0; i<resolution_list.length; i++){
        this.view2_resolution_list.push(resolution_list[i])
      }
    })
  },
  setup(){
    // 打印日志
    let mylog = (val)=>{
      let element = document.getElementById('mylog')
      let old_val = element.innerHTML
      let date = new Date().toString().slice(16, 24)
      element.innerHTML = date + '&nbsp;&nbsp;' + val + '<br>' + old_val;
    }

    // 添加缩略图
    let add_image = (img_base64)=>{
      let img = document.createElement('img');
      img.src = "data:image/jpg;base64," + img_base64;
      img.style.width = '80px';
      img.style.height = '80px';
      document.getElementById('suoluetu').appendChild(img)
    }

    let view1_mode_list = ref([])              // 主摄像头视频模式
    let view1_mode_selected = ref('1')         // 主摄像头视频模式当前选项
    let view1_resolution_list = ref([])        // 主摄像头分辨率
    let view1_resolution_selected = ref('')    // 主摄像头分辨率当前选项

    let view2_mode_list = ref([])              // 副摄像头视频模式
    let view2_mode_selected = ref('1')         // 副摄像头视频模式当前选项
    let view2_resolution_list = ref([])        // 副摄像头分辨率
    let view2_resolution_selected = ref('')    // 副摄像头分辨率当前选项

    // 切换主摄像头视频模式，重新加载主摄像头分辨率
    let view1_mode_change = (val)=>{
      let data = {"camidx": '0', "mode": val}
      axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(data)).then((res)=>{
        let resolution_list = res.data.data.split("|");
        view1_resolution_selected = resolution_list[0]
        view1_resolution_list = []
        for(var i=0; i<resolution_list.length; i++){
          view1_resolution_list.push(resolution_list[i])
        }
      })
    }

    // 切换副摄像头视频模式，重新加载副摄像头分辨率
    let view2_mode_change = (val)=>{
      let data = {"camidx": '1', "mode": val}
      axios.post("http://127.0.0.1:38088/device=getresolution", JSON.stringify(data)).then((res)=>{
        let resolution_list = res.data.data.split("|");
        view2_resolution_selected = resolution_list[0]
        view2_resolution_list = []
        for(var i=0; i<resolution_list.length; i++){
          view2_resolution_list.push(resolution_list[i])
        }
      })
    }

    // 打开主摄像头
    let open_view1 = ()=>{
      document.getElementById('view1').src = 'http://127.0.0.1:38088/video=stream&camidx=0?1'
      mylog('打开主摄像头成功')
    }

    // 关闭主摄像头
    let close_view1 = ()=>{
      let data = {"camidx": "0"}
      axios.post("http://127.0.0.1:38088/video=close", JSON.stringify(data)).then(()=>{
        document.getElementById('view1').src = ''
        mylog('关闭主摄像头成功')
      })
    }

    // 打开副摄像头
    let open_view2 = ()=>{
      document.getElementById('view2').src = 'http://127.0.0.1:38088/video=stream&camidx=1?1'
      mylog('打开副摄像头成功')
    }

    // 关闭副摄像头
    let close_view2 = ()=>{
      let data = {"camidx": "1"}
      axios.post("http://127.0.0.1:38088/video=close", JSON.stringify(data)).then(()=>{
        document.getElementById('view2').src = ''
        mylog('关闭副摄像头成功')
      })
    }

    // 旋转
    let rotate = (angle)=>{
      let data = {"camidx": '0', "rotate": String(angle)}
      axios.post("http://127.0.0.1:38088/video=rotate", JSON.stringify(data)).then((res)=>{
        mylog("旋转" + String(angle) + "度成功")
      })
    }

    // 主头拍照
    let view1_scan = ()=>{
      let data = {
        "filepath": "base64",
        "rotate": "0",
        "cutpage": "0",
        "camidx": "0",
        "ColorMode": "0",
        "quality": "3"
      }
      axios.post("http://127.0.0.1:38088/video=grabimage", JSON.stringify(data)).then((res)=>{
        add_image(res.data.photoBase64)
        mylog("主头拍照成功")
        mylog('图片base64： ' + res.data.photoBase64)
      })
    }

    // 副头拍照
    let view2_scan = ()=>{
      let data = {
        "filepath": "base64",
        "rotate": "0",
        "cutpage": "0",
        "camidx": "1",
        "ColorMode": "0",
        "quality": "3"
      }
      axios.post("http://127.0.0.1:38088/video=grabimage", JSON.stringify(data)).then((res)=>{
        add_image(res.data.photoBase64)
        mylog("副头拍照成功")
        mylog('图片base64： ' + res.data.photoBase64)
      })
    }

    // 展平拍照
    let flat_scan = ()=>{
      let data = {
        "filepath": "",
        "rotate": "0",
        "camidx": "0",
        "cutpage": "0",
        "autoflat": {
          "flat": "1",
          "leftfilepath": "D://left.jpg",
          "rightfilepath": "D://right.jpg",
          "removefinger": "1",
          "doublepage": "1"
        }
      }
      axios.post("http://127.0.0.1:38088/video=autoflat", JSON.stringify(data)).then((res)=>{
        add_image(res.data.photoBase64)
        add_image(res.data.leftphotoBase64)
        add_image(res.data.rightphotoBase64)
        mylog("展平拍照成功")
      })
    }

    // 开启自动拍照
    let open_auto_scan = ()=>{
      let data = {
        "movedetecflag": "1",
        "listpath": "D://a",
        "filepath": "hy"
      }
      axios.post("http://127.0.0.1:38088/video=movedetec", JSON.stringify(data)).then(()=>{
        add_image(res.data.data)
        mylog("这是自动拍摄的图片")
      })
    }

    // 关闭自动拍照
    let close_auto_scan = ()=>{
      let data = {"movedetecflag": "0"}
      axios.post("http://127.0.0.1:38088/video=movedetec", JSON.stringify(data)).then(()=>{
        mylog('关闭自动拍照成功')
      })
    }

    // 条码识别
    let getcode = ()=>{
      let data = {"time": "20"}
      axios.post("http://127.0.0.1:38088/barcode=get", JSON.stringify(data)).then((res)=>{
        for(let i=0; i<res.data.data.length; i++){
          mylog(res.data.data[i].barcodedata)
        }
        mylog("识别成功，条码数量" + res.data.data.length + "个，分别是：")
      })
    }

    // 获取指纹
    let getbiokey = ()=>{
      let data = {"time": "20"}
      axios.post("http://127.0.0.1:38088/biokey=get", JSON.stringify(data)).then((res)=>{
        add_image(res.data.data)
        mylog("获取指纹成功")
      })
    }

    // 读取身份证
    let getidcard = ()=>{
      axios.post("http://127.0.0.1:38088/card=idcard").then((res)=>{
        add_image(res.data.IDCardInfo.photoBase64)
        add_image(res.data.IDCardInfo.photoBase64_Z)
        add_image(res.data.IDCardInfo.photoBase64_F)
        mylog('身份证UID：' + res.data.IDCardInfo.strIDUID)
        mylog('身份证附加信息：' + res.data.IDCardInfo.appendMsg)
        mylog('身份证民族代码：' + res.data.IDCardInfo.nationCode)
        mylog('身份证性别代码：' + res.data.IDCardInfo.sexCode)
        mylog('身份证有效终止日期：' + res.data.IDCardInfo.validEnd)
        mylog('身份证有效起始日期：' + res.data.IDCardInfo.validStart)
        mylog('身份证发卡机构：' + res.data.IDCardInfo.issueOrgan)
        mylog('身份证号码：' + res.data.IDCardInfo.cardID)
        mylog('身份证地址：' + res.data.IDCardInfo.address)
        mylog('身份证生日：' + res.data.IDCardInfo.birthday)
        mylog('身份证性别：' + res.data.IDCardInfo.sex)
        mylog('身份证姓名：' + res.data.IDCardInfo.name)
      })
    }

    // 弹出签字窗口: GW500A & GW1000A
    let sign_a = ()=>{
      let data = {
        "pos": {
          "top": "250",
          "left": "280",
          "width": "600",
          "height": "250"
        },
        "remark": "开始签名"
      }
      axios.post("http://127.0.0.1:38088/serialport=sign", JSON.stringify(data)).then((res)=>{
        mylog(res.data.message)
      })
    }

    // 获取签字图片：GW500A & GW1000A
    let sign_a_get = ()=>{
      axios.post("http://127.0.0.1:38088/pendisplay=getsigndata").then((res)=>{
        add_image(res.data.data)
        mylog("获取签字图片成功")
      })
    }

    //---------------------------------------------视频录制-------------------------------------
    // 开始录制视频
    let start_video = ()=>{
      let data = {
        "action": "start",
        "parameter": {
          "camidx": "0",
          "width": "640",
          "height": "480",
          "audio": "",
          "framerate": "10",
          "filepath": "",
          "bit_rate": "400000"
        }
      }
      axios.post("http://127.0.0.1:38088/video=record", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog("视频录制中..., 文件存储地址：" + res.data.filepath)
        }else{
          mylog("开始录制失败")
        }
      })
    }

    // 结束录制视频
    let end_video = ()=>{
      let data = {"action": "stop"}
      axios.post("http://127.0.0.1:38088/video=record", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog('录制时长：' + res.data.time)
        }else{
          mylog("结束录制视频失败")
        }
      })
    }

    // 获取录制视频状态
    let get_state_video = ()=>{
      let data = {"action": "status"}
      axios.post("http://127.0.0.1:38088/video=record", JSON.stringify(data)).then((res)=>{
        mylog("提示：设备状态，100:空闲，101:录像中，102:设备错误")
        mylog("当前状态：" + res.data.status)
      })
    }

    // 获取音频列表
    let get_audio = ()=>{
      let data = {"action": "audio"}
      axios.post("http://127.0.0.1:38088/video=record", JSON.stringify(data)).then((res)=>{
        mylog("音频设备列表：" + res.data.audio)
      })
    }

    //---------------------------------------------A3A4幅面自动切换-----------------------------
    // 开启A3A4幅面自动切换
    let open_a3a4 = ()=>{
      let data = {
        "switchflag": "1",
        "a3size": "0.5",
        "a4size": "0.9"
      }
      axios.post("http://127.0.0.1:38088/device=a3a4switch", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog("开启幅面自动切换成功")
        }else{
          mylog("开启幅面自动切换失败")
        }
      })
    }

    // 关闭A3A4幅面自动切换
    let close_a3a4 = ()=>{
      let data = {
        "switchflag": "0",
        "a3size": "0.5",
        "a4size": "0.9"
      }
      axios.post("http://127.0.0.1:38088/device=a3a4switch", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog("关闭幅面自动切换成功")
        }else{
          mylog("关闭幅面自动切换失败")
        }
      })
    }

    //---------------------------------------------pdf-----------------------------------------
    // 拍照并加入PDF队列
    let add_pdf = ()=>{
      let data1 = {
        "filepath": "base64",
        "rotate": "0",
        "cutpage": "0",
        "camidx": "0",
        "quality": "5"
      }
      axios.post("http://127.0.0.1:38088/video=grabimage", JSON.stringify(data1)).then((res1)=>{
        if(res1.data.code == '0'){
          add_image(res1.data.photoBase64)
          
          let data2 = {
            "ImagePath": "",
            "ImageBase64": res1.data.photoBase64
          }
          axios.post("http://127.0.0.1:38088/pdf=addimage", JSON.stringify(data2)).then((res2)=>{
            if(res2.data.code == '0'){
              mylog("拍照成功，并加入到PDF队列中")
            }else{
              mylog("加入PDF队列失败")
            }
          })
        }else{
          mylog("拍照失败，请重新拍摄")
        }
      })
    }

    // 生成PDF文件
    let save_pdf = ()=>{
      let data = {"PdfPath": "D://pdf.pdf"}
      axios.post("http://127.0.0.1:38088/pdf=save", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog("PDF保存成功")
        }
      })
    }

    //---------------------------------------------人脸-----------------------------------------
    // 活体检测
    let is_living_person = ()=>{
      let data = {"time": "20"}
      axios.post("http://127.0.0.1:38088/faceLive=start", JSON.stringify(data)).then((res)=>{
        mylog("提示：比对结果，-1:失败；0:图片；1:成功")
        mylog("检测结果：" + res.data.data)
      })
    }

    // 人证比对
    let person_and_IDCard = ()=>{
      // 1.读取身份证
      axios.post("http://127.0.0.1:38088/card=idcard").then((res1)=>{
        if(res1.data.code == '0'){
          add_image(res1.data.IDCardInfo.photoBase64)
          // 2.拍摄人脸
          let data2 = {
            "filepath": "base64",
            "rotate": "0",
            "cutpage": "0",
            "camidx": "1",
            "quality": "5"
          }
          axios.post("http://127.0.0.1:38088/video=grabimage", JSON.stringify(data2)).then((res2)=>{
            add_image(res2.data.photoBase64)
            // 3.比对
            let data3 = {
              "FaceOne": res1.data.IDCardInfo.photoBase64,
              "FaceTwo": res2.data.photoBase64
            }
            axios.post("http://127.0.0.1:38088/comparison=imgdata", JSON.stringify(data3)).then((res3)=>{
              mylog("提示：比对值大于50可以认为是同一个人")
              mylog("比对值：" + res3.data.data)
            })
          })
        }else{
          mylog("请放身份证，重新点击此按钮")
        }
      })
    }

    // ocr
    let ocr = ()=>{
      // ocr 是从图片中识别的，所以需要先拍一张图片保存本地，然后在做ocr识别
      let data1 = {
        "filepath": "",
        "rotate": "0",
        "cutpage": "0",
        "camidx": "0"
      } 
      axios.post("http://127.0.0.1:38088/video=grabimage", JSON.stringify(data1)).then((res1)=>{
        add_image(res1.data.photoBase64)
        mylog("识别中。。。")
        let data2 = {
          "ocrflag": "1",
          "picfilepath": res1.data.filepath,
          "savefilepath": "D://ocr.pdf"
        }
        axios.post("http://127.0.0.1:38088/video=ocr", JSON.stringify(data2)).then((res2)=>{
          if(res2.data.code == '0'){
            mylog("识别成功")
          }else{
            mylog("识别失败")
          }
        })
      })
    }

    //---------------------------------------------设备-----------------------------------------
    // 获取设备型号
    let getequipmenttype = ()=>{
      axios.post("http://127.0.0.1:38088/device=getequipmenttype").then((res)=>{
        mylog("设备型号：" + res.data.data)
      })
    }

    // 获取设备序列号
    let getsonixserialnumber = ()=>{
      axios.post("http://127.0.0.1:38088/device=getsonixserialnumber").then((res)=>{
        mylog("设备序列号：" + res.data.data)
      })
    }

    // 获取设备状态
    let get_state = ()=>{
      axios.post("http://127.0.0.1:38088/video=status").then((res)=>{
        mylog("提示：no:未连接；ok:已连接；run:已连接且运行")
        mylog("副摄像头：" + res.data.video1)
        mylog("主摄像头：" + res.data.video0)
      })
    }

    // 判断设备是否连接
    let is_con = ()=>{
      axios.post("http://127.0.0.1:38088/device=isconnect").then((res)=>{
        mylog("设备连接数：" + res.data.data)
      })
    }

    //---------------------------------------------串口-----------------------------------------
    // 打开串口
    let open_serialport = ()=>{
      let data = {
        "port": "0",
        "baud": "115200",
        "parity": "0",
        "databits": "8",
        "stopbits": "0"
      }
      axios.post("http://127.0.0.1:38088/serialport=initserialport", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog("打开串口成功")
        }
      })
    }

    // 关闭串口
    let close_serialport = ()=>{
      let data = {"port": "0"}
      axios.post("http://127.0.0.1:38088/serialport=deinitserialport", JSON.stringify(data)).then((res)=>{
        if(res.data.code == '0'){
          mylog("关闭串口成功")
        }
      })
    }

    // 弹出签字窗口: GW500R & GW1000R
    let sign_r = ()=>{
      axios.post("http://127.0.0.1:38088/serialport=sign").then((res)=>{
        if(res.data.code == '0'){
          mylog('弹出签字窗口成功')
        }
      })
    }

    // 获取签名图片
    let sign_r_get = ()=>{
      axios.post("http://127.0.0.1:38088/serialport=getdata").then((res)=>{
        add_image(res.data.data)
        mylog("获取签名图片成功")
      })
    }

    return {
      mylog, add_image,
      view1_mode_list, view1_mode_selected, view1_resolution_list, view1_resolution_selected, 
      view2_mode_list, view2_mode_selected, view2_resolution_list, view2_resolution_selected,
      view1_mode_change, view2_mode_change,
      open_view1, close_view1, open_view2, close_view2, rotate,
      view1_scan, view2_scan, flat_scan, open_auto_scan, close_auto_scan,
      getcode, getbiokey, getidcard, sign_a, sign_a_get,
      start_video, end_video, get_state_video, get_audio,
      open_a3a4, close_a3a4, 
      add_pdf, save_pdf, 
      is_living_person, person_and_IDCard, ocr,
      getequipmenttype, getsonixserialnumber, get_state, is_con,
      open_serialport, close_serialport, sign_r, sign_r_get
    }
  }
})
</script>

<style>
/* 全局 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin-top: 10px;
}
/* 视频预览 */
#view1, #view2{
    width: 400px;
    height: 300px;
    border: 1px solid red;
    margin-right: 5px;
}
/* 缩略图 */
#suoluetu{
  width: 100%;
  height: 85px;
  border: 1px solid blue;
}
#suoluetu img{
  margin-right: 10px;
}
/* 操作按钮 */
#myactive{
  border: 1px solid yellowgreen;
  margin-top: 10px;
  padding: 10px 5px;
}
/* 操作日志 */
#mylog{
  border: 1px solid black;
  padding: 10px;
  margin-top: 10px;
  overflow: auto;
}
</style>
