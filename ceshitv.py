import cv2

def record_video():
    # 定义保存视频的格式
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # 创建VideoWriter对象，设置输出文件名称和格式
    out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

    # 调用默认摄像头
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        # 从摄像头读取图像
        ret, frame = cap.read()
        if ret:
            # 将帧写入到视频文件
            out.write(frame)

            # 显示图像
            cv2.imshow('frame', frame)

            # 按'q'键退出循环
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    # 释放资源q
    # 释放资源
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    record_video()

