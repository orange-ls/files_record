```
Function 下载表格文件(thisRow,excelName)
	Log.Info("点击下载按钮")
	#icon("@res:default.png")
	rowAry = UiElement.GetChildren(thisRow,{"bContinueOnError":False,"iDelayAfter":300,"iDelayBefore":200})
	dAry = UiElement.GetChildren(rowAry[3],{"bContinueOnError":False,"iDelayAfter":300,"iDelayBefore":200})
	// TracePrint(dAry)
	downloadButton = UiElement.GetChildren(dAry[0],{"bContinueOnError":False,"iDelayAfter":300,"iDelayBefore":200})
	TracePrint(downloadButton)
	#icon("@res:default.png")
	Mouse.Action(downloadButton[0],"left","click",10000,{"bContinueOnError":False,"iDelayAfter":300,"iDelayBefore":200,"bSetForeground":True,"sCursorPosition":"Center","iCursorOffsetX":0,"iCursorOffsetY":0,"sKeyModifiers":[],"sSimulate":"simulate","bMoveSmoothly":False})
	Log.Info("移动表格文件到目标文件夹")
    // dFile = g_dictGlobal["Chrome下载路径"] & "\\" & excelName & "_" & Time.Format(Time.Now(),"yyyymmdd") & ".xlsx"
    dFile = excelName & "_" & Time.Format(Time.Now(),"yyyymmdd") & "*"
    // 等待表格下载完成，最多等待5分钟
	For i=0 To 150
		Delay(2000)
		// bRet = File.FileExists(dFile)
        // 查找匹配模式的文件
        arrFiles = File.SearchFile(g_dictGlobal["Chrome下载路径"],dFile,true)
		// 遍历文件，查找匹配的文件
        If Len(arrFiles) > 0
            dFile = arrFiles[Len(arrFiles)-1]
            Break
        End If
	Next
	File.MoveFile(dFile, g_dictGlobal["云服务中间数据存放文件夹"],False)
End Function
```



```
g_dictGlobal["退货-华为"] = GetCrmFileName(g_dictGlobal["云服务中间数据存放文件夹"], "退货-华为对象导出结果_" & Time.Format(Time.Now(),"yyyymmdd"))
g_dictGlobal["厂商PO号"] = GetCrmFileName(g_dictGlobal["云服务中间数据存放文件夹"], "厂商PO号对象导出结果_" & Time.Format(Time.Now(),"yyyymmdd"))
	
```



```
/*
功能：读取账号密码配置表中的数据
入参: dir_path -- 文件地址
      file_name -- 文件名称
出参：返回匹配的文件名
*/
Function GetCrmFileName(dir_path,file_name)
	dFile = dir_path & "\\" & file_name & ".xlsx"
	// 查找匹配模式的文件
    file_name = file_name  & "*"
	arrFiles = File.SearchFile(dir_path,file_name,True)
	// 遍历文件，查找匹配的文件
	If Len(arrFiles) > 0
		dFile = arrFiles[Len(arrFiles)-1]
	End If
	Return dFile
End Function

```

